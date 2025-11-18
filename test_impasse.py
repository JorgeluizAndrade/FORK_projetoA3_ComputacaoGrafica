import sys
import os

# Adiciona pasta atual para achar a DLL
try:
    os.add_dll_directory(os.getcwd())
except AttributeError:
    pass

try:
    import impasse
    print("Biblioteca 'impasse' encontrada.")
except ImportError:
    print("ERRO: Instale com 'pip install impasse'")
    sys.exit()

path = 'assets/models/character.fbx'

if not os.path.exists(path):
    print(f"ARQUIVO NÃO ENCONTRADO: {path}")
    sys.exit()

try:
    print(f"Carregando: {path}...")
    
    # CORREÇÃO: Carregar direto, sem 'with'
    scene = impasse.load(path)
    
    print("-" * 30)
    print("SUCESSO! Modelo carregado com IMPASSE.")
    print(f"Malhas: {len(scene.meshes)}")
    
    if len(scene.meshes) > 0:
        mesh = scene.meshes[0]
        print(f"Vértices: {len(mesh.vertices)}")
        
        # O TESTE DE FOGO:
        print(f"Ossos (Bones): {len(mesh.bones)}")
        
        if len(mesh.bones) > 0:
            print("--> ESQUELETO ENCONTRADO! (Problema Resolvido)")
        else:
            print("--> SEM ESQUELETO. Verifique se baixou a ANIMAÇÃO no Mixamo com 'With Skin'.")

    # Liberar memória (opcional no Python moderno, mas bom saber)
    # scene.release() 

except Exception as e:
    print("-" * 30)
    print(f"ERRO: {e}")