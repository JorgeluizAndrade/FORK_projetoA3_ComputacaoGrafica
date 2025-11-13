import glfw
from OpenGL.GL import *
import settings # As constantes

class Engine:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # 1. Inicializar o glfw
        if not glfw.init():
            raise Exception("GLFW não pôde ser inicializado.")
        
        # 2. Configurar a Janela com OpenGl Moderno
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1) #OpenGL 4.1
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE) # macOS
        
        # 3. Criar a Janela
        self.window = glfw.create_window(self.width, self.height, "Projeto A3 - OpenGL", None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("A janela não pôde ser criada")
        
        # Tornar o contexto da janela o principal
        glfw.make_context_current(self.window)
        
    def run(self):
        
        # 4. Implementar o Loop (Manter o programa rodando)
        while not glfw.window_should_close(self.window):
            
            # Verificar eventos (Como fechar a janela)
            glfw.poll_events()
            
            # Definir a cor do mundo (Azul)
            glClearColor(0.1, 0.4, 0.7, 1.0)
            
            # limpar a tela antes de desenhar um novo quadro
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # Mostrar o que foi desenhado
            glfw.swap_buffers(self.window)
            
        #Finalizar
        glfw.terminate()
        
if __name__ == "__main__":
    # Iniciar a aplicação
    engine = Engine(settings.WIN_WIDTH, settings.WIN_HEIGHT)
    print("Aplicação iniciada. Executando...")
    engine.run()
    print("Aplicação Finalizada.")