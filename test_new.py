import sys
import os
import assimp_py

print("Biblioteca assimp-py carregada.")

path = 'assets/models/character.fbx'

if not os.path.exists(path):
    print(f"ERRO: Arquivo não encontrado em {path}")
    sys.exit()

try:
    print(f"Tentando carregar: {path}...")
    
    # CORREÇÃO: Usando 'import_file' (minúsculo)
    # Flags: Triangulatar e gerar tangentes
    flags = assimp_py.Process_Triangulate | assimp_py.Process_CalcTangentSpace
    
    scene = assimp_py.import_file(path, flags)
    
    print("-" * 30)
    print("SUCESSO! Modelo carregado.")
    print(f"Malhas: {len(scene.meshes)}")
    print(f"Materiais: {len(scene.materials)}")
    
    # Verifica o nome do nó raiz (para saber se usamos .root_node ou .rootnode no futuro)
    # Tenta acessar atributos comuns para garantir
    if hasattr(scene, 'root_node'):
        print("Atributo de raiz: scene.root_node (OK)")
    elif hasattr(scene, 'rootnode'):
        print("Atributo de raiz: scene.rootnode (OK)")
    else:
        print("AVISO: Não encontrei o nome do nó raiz. Vamos descobrir depois.")

    print("-" * 30)

except Exception as e:
    print(f"ERRO: {e}")