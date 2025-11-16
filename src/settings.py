import glm

# Constantes globais

# dimensões da tela
WIN_WIDTH = 1280
WIN_HEIGHT = 720

# Constantes da física
GRAVITY = -9.8
JUMP_FORCE = 5.0

# Constantes de terreno
MAX_TERRAIN_HEIGHT = 40.0

# Novas Constantes da Câmera
CAMERA_SPEED = 5.0 # Metros por segundo
CAMERA_RUN_MULTIPLIER = 2.0
CAMERA_SENSITIVITY = 0.1

# Configurações do Terreno
TERRAIN_SIZE = 300.0 # O PDF pede >= 300m (Regra 1.a)

# Paleta de cores para o céu
COLOR_DAY = glm.vec3(0.5, 0.7, 1.0) # Azul claro
COLOR_SUNSET = glm.vec3(1.0, 0.5, 0.2) # Laranja
COLOR_NIGHT = glm.vec3(0.0, 0.0, 0.05) # Azul muito escuro