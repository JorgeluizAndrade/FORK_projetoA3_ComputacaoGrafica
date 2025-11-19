import struct
import numpy as np
from OpenGL.GL import *
import ctypes
from pygltflib import GLTF2
import glm

class Mesh:
    def __init__(self, vertices, indices):
        self.vertices = vertices # Dados intercalados (Pos, Norm, UV, Bones, Weights)
        self.indices = indices
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)
        self.setup_mesh()

    def setup_mesh(self):
        if len(self.vertices) == 0: return

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        
        if len(self.indices) > 0:
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        # Layout deve bater com o Shader: 
        # 0:Pos(3f), 1:Norm(3f), 2:UV(2f), 3:BoneIDs(4i), 4:Weights(4f)
        stride = 64 # (3+3+2+4+4) * 4 bytes = 64
        
        # Posição
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        # Normal
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        # UV
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
        # Bone IDs (Inteiros!)
        glEnableVertexAttribArray(3)
        glVertexAttribIPointer(3, 4, GL_INT, stride, ctypes.c_void_p(32))
        # Pesos
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(48))
        
        glBindVertexArray(0)

    def draw(self, shader):
        glBindVertexArray(self.vao)
        if len(self.indices) > 0:
            glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        else:
            # Caso não tenha índices (raro em GLB, mas possível)
            glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 16)
        glBindVertexArray(0)

class Model:
    def __init__(self, path, shader):
        self.shader = shader
        self.meshes = []
        self.load_glb(path)

    def load_glb(self, path):
        print(f"--- CARREGANDO GLB: {path} ---")
        try:
            gltf = GLTF2().load(path)
            
            # Itera sobre todas as malhas do arquivo
            for mesh_idx, gltf_mesh in enumerate(gltf.meshes):
                print(f"Processando Malha {mesh_idx}: {gltf_mesh.name}")
                
                for primitive in gltf_mesh.primitives:
                    # 1. Extrair Atributos
                    pos = self.get_data(gltf, primitive.attributes.POSITION, 3)
                    norm = self.get_data(gltf, primitive.attributes.NORMAL, 3)
                    uv = self.get_data(gltf, primitive.attributes.TEXCOORD_0, 2)
                    joints = self.get_data(gltf, primitive.attributes.JOINTS_0, 4, dtype=np.int32)
                    weights = self.get_data(gltf, primitive.attributes.WEIGHTS_0, 4)
                    
                    # Verifica contagem de vértices
                    num_v = len(pos)
                    
                    # Preenche dados faltantes com zeros se necessário
                    if len(norm) == 0: norm = np.zeros((num_v, 3), dtype=np.float32)
                    if len(uv) == 0: uv = np.zeros((num_v, 2), dtype=np.float32)
                    if len(joints) == 0: joints = np.zeros((num_v, 4), dtype=np.int32)
                    if len(weights) == 0: weights = np.zeros((num_v, 4), dtype=np.float32)

                    # 2. Extrair Índices
                    if primitive.indices is not None:
                        indices = self.get_data(gltf, primitive.indices, 1, dtype=np.uint32).flatten()
                    else:
                        indices = np.array([], dtype=np.uint32)

                    # 3. Intercalar (Mesmo padrão do código antigo)
                    # Nota: Joints devem ser float no buffer intercalado para o numpy, 
                    # mas o glVertexAttribIPointer vai ler como int depois.
                    data = np.column_stack((pos, norm, uv, joints.astype(np.float32), weights))
                    v_data = data.flatten().astype(np.float32)

                    print(f"  > Primitiva: {num_v} vértices, {len(indices)//3} triângulos.")
                    self.meshes.append(Mesh(v_data, indices))
            
            print("--- MODELO CARREGADO COM SUCESSO ---")

        except Exception as e:
            print(f"ERRO AO CARREGAR GLB: {e}")
            import traceback
            traceback.print_exc()

    def get_data(self, gltf, accessor_idx, comp_count, dtype=np.float32):
        """Extrai dados binários do GLB para NumPy Array"""
        if accessor_idx is None: return np.array([])
        
        accessor = gltf.accessors[accessor_idx]
        buffer_view = gltf.bufferViews[accessor.bufferView]
        
        # Pega os bytes brutos do blob binário
        # Nota: buffer_view.byteOffset é relativo ao buffer, mas em GLB geralmente só tem 1 buffer
        offset = buffer_view.byteOffset + (accessor.byteOffset or 0)
        length = buffer_view.byteLength
        
        # Em arquivos .glb, o buffer 0 é o binário embutido
        if gltf.buffers[buffer_view.buffer].uri is None:
            blob = gltf.binary_blob()
            if blob is None: return np.array([])
            raw_data = blob[offset : offset + length]
        else:
            print("Erro: Buffer externo URI não suportado neste script simples.")
            return np.array([])

        # Converte bytes para números
        # Mapa de tipos do GLTF componentType
        # 5126=FLOAT, 5123=USHORT, 5125=UINT, 5121=UBYTE
        cnt = accessor.count
        
        if accessor.componentType == 5126: # Float32
            arr = np.frombuffer(raw_data, dtype=np.float32)
        elif accessor.componentType == 5123: # UShort
            arr = np.frombuffer(raw_data, dtype=np.uint16).astype(dtype)
        elif accessor.componentType == 5125: # UInt
            arr = np.frombuffer(raw_data, dtype=np.uint32).astype(dtype)
        elif accessor.componentType == 5121: # UByte (Comum para joints/weights compactados)
            arr = np.frombuffer(raw_data, dtype=np.uint8).astype(dtype)
        else:
            print(f"Aviso: Tipo de componente {accessor.componentType} não tratado, retornando zeros.")
            return np.zeros((cnt, comp_count), dtype=dtype)

        # Redimensionar para (N, 3), (N, 2), etc.
        if comp_count > 1:
            return arr.reshape((-1, comp_count))
        return arr

    def draw(self, shader):
        for mesh in self.meshes:
            mesh.draw(shader)