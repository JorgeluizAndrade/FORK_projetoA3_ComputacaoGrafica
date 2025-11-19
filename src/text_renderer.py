import os
import freetype
from OpenGL.GL import *
import numpy as np

class TextRenderer:
    def __init__(self, font_path, size):
        font_path = os.path.normpath(font_path)
        print("Carregando fonte:", font_path)

        if not os.path.isfile(font_path):
            raise FileNotFoundError(f"Arquivo de fonte não encontrado: {font_path}")

        # Carrega a fonte
        self.face = freetype.Face(font_path)
        self.face.set_pixel_sizes(0, size)

        self.chars = {}
        self._load_characters()

        # Prepara VAO/VBO
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)

        # 4 floats por vértice (x, y, u, v)
        glBufferData(GL_ARRAY_BUFFER, 6 * 4 * 4, None, GL_DYNAMIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 4 * 4, ctypes.c_void_p(0))

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def _load_characters(self):
        for c in range(128):  
            self.face.load_char(chr(c))
            bitmap = self.face.glyph.bitmap

            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

            glTexImage2D(
                GL_TEXTURE_2D,
                0,
                GL_RED,
                bitmap.width,
                bitmap.rows,
                0,
                GL_RED,
                GL_UNSIGNED_BYTE,
                bitmap.buffer
            )

            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

            self.chars[chr(c)] = {
                "texture": tex_id,
                "size": (bitmap.width, bitmap.rows),
                "bearing": (self.face.glyph.bitmap_left, self.face.glyph.bitmap_top),
                "advance": self.face.glyph.advance.x
            }

    def render_text(self, shader, text, x, y, scale=1.0, color=(1,1,1)):
        shader.use()
        shader.set_uniform_vec3("textColor", color)

        glActiveTexture(GL_TEXTURE0)
        glBindVertexArray(self.vao)

        for char in text:
            ch = self.chars.get(char)
            if not ch:
                continue

            w, h = ch["size"]
            bx, by = ch["bearing"]

            xpos = x + bx * scale
            ypos = y - (h - by) * scale

            w *= scale
            h *= scale

            vertices = np.array([
                xpos,     ypos + h,   0.0, 0.0,
                xpos,     ypos,       0.0, 1.0,
                xpos + w, ypos,       1.0, 1.0,

                xpos,     ypos + h,   0.0, 0.0,
                xpos + w, ypos,       1.0, 1.0,
                xpos + w, ypos + h,   1.0, 0.0,
            ], dtype=np.float32)

            glBindTexture(GL_TEXTURE_2D, ch["texture"])
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
            glBufferSubData(GL_ARRAY_BUFFER, 0, vertices.nbytes, vertices)

            glDrawArrays(GL_TRIANGLES, 0, 6)

            x += (ch["advance"] >> 6) * scale

        glBindVertexArray(0)
        glBindTexture(GL_TEXTURE_2D, 0)
