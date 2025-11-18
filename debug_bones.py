import assimp_py
import sys

path = "assets/models/character.fbx"

try:
    print(f"Verificando: {path}...")
    # Flags essenciais para skinning
    flags = assimp_py.Process_Triangulate | assimp_py.Process_LimitBoneWeights
    
    scene = assimp_py.import_file(path, flags)
    mesh = scene.meshes[0]

    print("-" * 30)
    print(f"Malha: {mesh.name}")
    print(f"Vértices: {len(mesh.vertices)}")
    
    # Verifica se existe o atributo bones (de várias formas)
    has_bones = hasattr(mesh, 'bones')
    print(f"Atributo 'bones' existe? {has_bones}")
    
    if has_bones:
        print(f"Quantidade de Ossos: {len(mesh.bones)}")
        if len(mesh.bones) > 0:
            print(f"Exemplo de osso: {mesh.bones[0].name}")
            print(f"Pesos no primeiro osso: {len(mesh.bones[0].weights)}")
    else:
        # Tenta achar com outros nomes
        print("Procurando atributos com 'bone' no nome:")
        found = False
        for attr in dir(mesh):
            if 'bone' in attr.lower():
                print(f" -> Encontrado: {attr}")
                found = True
        if not found:
            print(" -> NENHUM atributo de osso encontrado.")

    print("-" * 30)
    print(f"Animações na Cena: {len(scene.animations)}")
    if len(scene.animations) > 0:
        anim = scene.animations[0]
        print(f"Nome da Animação: {anim.name}")
        print(f"Duração (Ticks): {anim.duration}")
    print("-" * 30)

except Exception as e:
    print(f"Erro: {e}")