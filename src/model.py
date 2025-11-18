from OpenGL.GL import *
import numpy as np
import ctypes
import impasse
import glm

class Mesh:
    def __init__(self, vertices, indices):
        self.vertices = vertices
        self.indices = indices
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)
        self.setup_mesh()

    def setup_mesh(self):
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_STATIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)

        stride = 64
        # 0: Pos, 1: Norm, 2: UV, 3: BoneIDs, 4: Weights
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
        glEnableVertexAttribArray(3)
        glVertexAttribIPointer(3, 4, GL_INT, stride, ctypes.c_void_p(32))
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(48))
        glBindVertexArray(0)

    def draw(self, shader):
        glBindVertexArray(self.vao)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

class Model:
    def __init__(self, path, shader):
        self.shader = shader
        self.meshes = []
        self.bone_map = {}
        self.bone_info = []
        self.bone_counter = 0
        self.load_model(path)

    def load_model(self, path):
        print(f"Carregando modelo (impasse): {path}...")
        try:
            scene = impasse.load(path)
            
            # Tenta processar via nó raiz, se falhar, vai direto nas malhas
            root = getattr(scene, 'root_node', getattr(scene, 'rootnode', None))
            
            if root:
                print("Processando via Nó Raiz...")
                self.process_node(root, scene)
            elif hasattr(scene, 'meshes') and len(scene.meshes) > 0:
                print("Raiz não encontrada. Processando malhas diretamente...")
                for mesh in scene.meshes:
                    self.meshes.append(self.process_mesh(mesh, scene))
            else:
                print("ERRO CRÍTICO: Nenhuma malha encontrada no arquivo.")
                return

            print(f"Modelo carregado! Malhas: {len(self.meshes)} | Ossos: {self.bone_counter}")
            # Nota: Não chamamos scene.release() no impasse
            
        except Exception as e:
            print(f"ERRO CRÍTICO no Model: {e}")
            # Não damos raise para não fechar a janela imediatamente

    def process_node(self, node, scene):
        # Se tiver malhas no nó, processa
        if hasattr(node, 'meshes'):
            for i in node.meshes:
                self.meshes.append(self.process_mesh(scene.meshes[i], scene))
        # Repete para filhos
        for child in node.children:
            self.process_node(child, scene)

    def process_mesh(self, mesh, scene):
        num_v = len(mesh.vertices)
        
        # Vértices
        pos = np.array(mesh.vertices, dtype=np.float32)
        
        # Normais
        norm = np.zeros((num_v, 3), dtype=np.float32)
        if hasattr(mesh, 'normals') and len(mesh.normals) > 0:
            norm = np.array(mesh.normals, dtype=np.float32)

        # UVs
        uv = np.zeros((num_v, 2), dtype=np.float32)
        # impasse: 'texturecoords' é lista de canais
        if hasattr(mesh, 'texturecoords') and mesh.texturecoords:
            channel0 = mesh.texturecoords[0]
            if channel0 is not None and len(channel0) > 0:
                raw_uv = np.array(channel0, dtype=np.float32)
                if raw_uv.shape[1] > 2: uv = raw_uv[:, :2]
                else: uv = raw_uv

        # Ossos
        b_ids = np.zeros((num_v, 4), dtype=np.int32)
        weights = np.zeros((num_v, 4), dtype=np.float32)

        if hasattr(mesh, 'bones'):
            for bone in mesh.bones:
                if bone.name not in self.bone_map:
                    self.bone_map[bone.name] = self.bone_counter
                    self.bone_counter += 1
                    # Transpor para OpenGL
                    offset = np.array(bone.offsetmatrix, dtype=np.float32).transpose()
                    self.bone_info.append(offset)
                
                idx = self.bone_map[bone.name]
                for w in bone.weights:
                    if w.weight == 0: continue
                    for k in range(4):
                        if weights[w.vertexid][k] == 0.0:
                            weights[w.vertexid][k] = w.weight
                            b_ids[w.vertexid][k] = idx
                            break

        # Índices (Faces) - impasse usa 'faces'
        indices_list = []
        if hasattr(mesh, 'faces'):
            for f in mesh.faces:
                indices_list.extend(f)
        elif hasattr(mesh, 'indices'):
            indices_list = mesh.indices
            
        idx_data = np.array(indices_list, dtype=np.uint32)
        
        # Intercalar
        interleaved = np.column_stack((pos, norm, uv, b_ids.astype(np.float32), weights))
        v_data = interleaved.flatten().astype(np.float32)

        return Mesh(v_data, idx_data)

    def draw(self, shader):
        for mesh in self.meshes:
            mesh.draw(shader)