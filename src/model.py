import struct
import numpy as np
from OpenGL.GL import *
import ctypes
from pygltflib import GLTF2
import glm
import io
from PIL import Image # Biblioteca para ler a textura

# --- CLASSE AUXILIAR PARA ANIMAÇÃO ---
class Node:
    def __init__(self, index, name, local_matrix=glm.mat4(1.0)):
        self.index = index
        self.name = name
        self.children = []
        self.parent = None
        
        # Transformações Locais (Animáveis)
        self.translation = glm.vec3(0.0)
        self.rotation = glm.quat(1.0, 0.0, 0.0, 0.0)
        self.scale = glm.vec3(1.0)
        
        self.local_transform = local_matrix
        self.global_transform = glm.mat4(1.0)
        self.inverse_bind_matrix = glm.mat4(1.0)
        self.is_joint = False

    def update_local_transform(self):
        t = glm.translate(glm.mat4(1.0), self.translation)
        r = glm.mat4(self.rotation)
        s = glm.scale(glm.mat4(1.0), self.scale)
        self.local_transform = t * r * s

class Mesh:
    def __init__(self, vertices, indices, texture_id=None):
        self.vertices = vertices
        self.indices = indices
        self.texture_id = texture_id # ID da textura OpenGL
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

        stride = 64
        # 0:Pos, 1:Norm, 2:UV, 3:BoneIDs, 4:Weights
        
        # Atributos 0, 1, 2 (Padrão)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(12))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(24))
        
        # --- CORREÇÃO CRÍTICA AQUI ---
        # Mudamos de glVertexAttribIPointer (Int) para Pointer (Float)
        # Isso resolve o "Cilindro"
        glEnableVertexAttribArray(3)
        glVertexAttribPointer(3, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(32)) 
        
        glEnableVertexAttribArray(4)
        glVertexAttribPointer(4, 4, GL_FLOAT, GL_FALSE, stride, ctypes.c_void_p(48))
        
        glBindVertexArray(0)

    def draw(self, shader):
        # Ativar Textura se existir
        if self.texture_id is not None:
            glActiveTexture(GL_TEXTURE0) # Unidade 0 para cor difusa
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            shader.set_uniform_int("u_texture_diffuse", 0)
            shader.set_uniform_int("u_has_texture", 1)
        else:
            shader.set_uniform_int("u_has_texture", 0)

        glBindVertexArray(self.vao)
        if len(self.indices) > 0:
            glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)
        else:
            glDrawArrays(GL_TRIANGLES, 0, len(self.vertices) // 16)
        glBindVertexArray(0)

class Model:
    def __init__(self, path, shader):
        self.shader = shader
        self.meshes = []
        self.nodes = []
        self.root_nodes = []
        self.joints = []
        self.animations = [] 
        self.current_time = 0.0
        self.textures = {} # Mapa de índice GLTF -> ID OpenGL
        
        self.load_glb(path)

    def update_animation(self, delta_time):
        if not self.animations: return # Se não tiver animação, não faz nada

        anim = self.animations[0]
        self.current_time += delta_time
        if self.current_time > anim['duration']: self.current_time = 0.0
        
        for channel in anim['channels']:
            node = self.nodes[channel['node_idx']]
            times = channel['times']
            values = channel['values']
            path = channel['path']
            
            # Busca binária ou linear simples
            k = 0
            for i in range(len(times) - 1):
                if self.current_time >= times[i] and self.current_time <= times[i+1]:
                    k = i
                    break
            
            dt = times[k+1] - times[k]
            factor = (self.current_time - times[k]) / dt if dt > 0 else 0.0
            
            if path == 'translation':
                idx = k * 3
                v0 = glm.vec3(values[idx], values[idx+1], values[idx+2])
                idx = (k+1) * 3
                v1 = glm.vec3(values[idx], values[idx+1], values[idx+2])
                node.translation = glm.mix(v0, v1, factor)
            elif path == 'rotation':
                idx = k * 4
                q0 = glm.quat(values[idx+3], values[idx], values[idx+1], values[idx+2])
                idx = (k+1) * 4
                q1 = glm.quat(values[idx+3], values[idx], values[idx+1], values[idx+2])
                node.rotation = glm.slerp(q0, q1, factor)
            elif path == 'scale':
                idx = k * 3
                v0 = glm.vec3(values[idx], values[idx+1], values[idx+2])
                idx = (k+1) * 3
                v1 = glm.vec3(values[idx], values[idx+1], values[idx+2])
                node.scale = glm.mix(v0, v1, factor)

        self.update_hierarchy()

    def update_hierarchy(self):
        for node in self.nodes: node.update_local_transform()
        for root in self.root_nodes: self.update_node_global(root, glm.mat4(1.0))

    def update_node_global(self, node, parent_transform):
        node.global_transform = parent_transform * node.local_transform
        for child_idx in node.children:
            self.update_node_global(self.nodes[child_idx], node.global_transform)

    def draw(self, shader):
        bone_matrices = []
        if self.joints:
            for joint_idx in self.joints:
                node = self.nodes[joint_idx]
                bone_matrices.append(node.global_transform * node.inverse_bind_matrix)
            if len(bone_matrices) > 100: bone_matrices = bone_matrices[:100]
            shader.set_uniform_mat4_array("u_finalBones", bone_matrices)
        else:
            # Envia Identidade se não tiver ossos, para o shader não bugar
            shader.set_uniform_mat4_array("u_finalBones", [glm.mat4(1.0)] * 100)

        for mesh in self.meshes:
            mesh.draw(shader)

    def load_glb(self, path):
        print(f"Carregando: {path}...")
        try:
            gltf = GLTF2().load(path)
            
            # 1. Carregar Texturas (NOVO)
            if gltf.images:
                print(f"Processando {len(gltf.images)} texturas...")
                for i, img_entry in enumerate(gltf.images):
                    tex_id = self.process_texture(gltf, img_entry)
                    if tex_id: self.textures[i] = tex_id

            # 2. Nós e Hierarquia
            for i, g_node in enumerate(gltf.nodes):
                node = Node(i, g_node.name or f"Node_{i}")
                if g_node.translation: node.translation = glm.vec3(*g_node.translation)
                if g_node.rotation: node.rotation = glm.quat(g_node.rotation[3], g_node.rotation[0], g_node.rotation[1], g_node.rotation[2])
                if g_node.scale: node.scale = glm.vec3(*g_node.scale)
                node.children = g_node.children or []
                self.nodes.append(node)
            
            children_ids = set()
            for node in self.nodes:
                for c in node.children: 
                    self.nodes[c].parent = node
                    children_ids.add(c)
            self.root_nodes = [n for i, n in enumerate(self.nodes) if i not in children_ids]

            # 3. Skins
            if gltf.skins:
                skin = gltf.skins[0]
                self.joints = skin.joints
                if skin.inverseBindMatrices is not None:
                    data = self.get_data(gltf, skin.inverseBindMatrices, 16)
                    for k, j_idx in enumerate(self.joints):
                        raw_m = data[k]
                        self.nodes[j_idx].inverse_bind_matrix = glm.make_mat4(raw_m.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))

            # 4. Malhas e Materiais
            for gltf_mesh in gltf.meshes:
                for prim in gltf_mesh.primitives:
                    # Geometria
                    pos = self.get_data(gltf, prim.attributes.POSITION, 3)
                    norm = self.get_data(gltf, prim.attributes.NORMAL, 3)
                    uv = self.get_data(gltf, prim.attributes.TEXCOORD_0, 2)
                    joints = self.get_data(gltf, prim.attributes.JOINTS_0, 4, np.uint32)
                    weights = self.get_data(gltf, prim.attributes.WEIGHTS_0, 4)
                    indices = self.get_data(gltf, prim.indices, 1, np.uint32).flatten() if prim.indices is not None else np.array([], dtype=np.uint32)
                    
                    # Padding
                    nv = len(pos)
                    if len(norm)==0: norm=np.zeros((nv,3), np.float32)
                    if len(uv)==0: uv=np.zeros((nv,2), np.float32)
                    if len(joints)==0: joints=np.zeros((nv,4), np.uint32)
                    if len(weights)==0: weights=np.zeros((nv,4), np.float32)

                    data = np.column_stack((pos, norm, uv, joints.astype(np.float32), weights))
                    v_data = data.flatten().astype(np.float32)
                    
                    # Descobrir Textura do Material
                    tex_id = None
                    if prim.material is not None:
                        mat = gltf.materials[prim.material]
                        if mat.pbrMetallicRoughness and mat.pbrMetallicRoughness.baseColorTexture:
                            tex_idx = mat.pbrMetallicRoughness.baseColorTexture.index
                            # O índice da textura aponta para uma 'source' (imagem)
                            source_img_idx = gltf.textures[tex_idx].source
                            tex_id = self.textures.get(source_img_idx)

                    self.meshes.append(Mesh(v_data, indices, tex_id))

            # 5. Animação
            if gltf.animations:
                for g_anim in gltf.animations:
                    anim = {'channels': [], 'duration': 0.0}
                    for ch in g_anim.channels:
                        sampler = g_anim.samplers[ch.sampler]
                        times = self.get_data(gltf, sampler.input, 1).flatten()
                        vals = self.get_data(gltf, sampler.output, 4 if ch.target.path=='rotation' else 3).flatten()
                        anim['channels'].append({'node_idx': ch.target.node, 'path': ch.target.path, 'times': times, 'values': vals})
                        if len(times)>0: anim['duration'] = max(anim['duration'], times[-1])
                    self.animations.append(anim)

            print("Modelo carregado com sucesso!")
        except Exception as e:
            print(f"Erro GLB: {e}")
            import traceback
            traceback.print_exc()

    def process_texture(self, gltf, img_entry):
        try:
            if img_entry.bufferView is None: return None
            
            bv = gltf.bufferViews[img_entry.bufferView]
            offset = bv.byteOffset + (0)
            blob = gltf.binary_blob()
            img_data = blob[offset : offset + bv.byteLength]
            
            image = Image.open(io.BytesIO(img_data))
            
            # --- CORREÇÃO DE COR ---
            # Removi o FLIP_TOP_BOTTOM. O GLB geralmente já vem correto.
            # Se continuar errado, tente descomentar a linha abaixo:
            # image = image.transpose(Image.FLIP_TOP_BOTTOM) 
            
            if image.mode != 'RGBA': image = image.convert('RGBA')
            img_bytes = image.tobytes()
            
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, image.width, image.height, 0, GL_RGBA, GL_UNSIGNED_BYTE, img_bytes)
            glGenerateMipmap(GL_TEXTURE_2D)
            return tex_id
        except Exception as e:
            print(f"Erro textura: {e}")
            return None

    def get_data(self, gltf, acc_idx, comp, dtype=np.float32):
        if acc_idx is None: return np.array([])
        acc = gltf.accessors[acc_idx]
        bv = gltf.bufferViews[acc.bufferView]
        off = bv.byteOffset + (acc.byteOffset or 0)
        blob = gltf.binary_blob()
        raw = blob[off : off + bv.byteLength]
        
        if acc.componentType==5126: arr = np.frombuffer(raw, dtype=np.float32)
        elif acc.componentType==5123: arr = np.frombuffer(raw, dtype=np.uint16).astype(dtype)
        elif acc.componentType==5125: arr = np.frombuffer(raw, dtype=np.uint32).astype(dtype)
        elif acc.componentType==5121: arr = np.frombuffer(raw, dtype=np.uint8).astype(dtype)
        else: return np.zeros((acc.count, comp), dtype=dtype)
        
        if comp > 1: return arr.reshape((-1, comp))
        return arr