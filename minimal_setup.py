from __future__ import division
import pygame
from pygame.locals import *

from OpenGL.GL import * 
from OpenGL.GL import shaders
#from OpenGL.GLU import *

from sys import exit as exitsystem

from numpy import array


VERTEX_SHADER = """
#version 330 core

layout(location = 0) in vec3 vPos;

void main()
{
    gl_Position = vec4(vPos, 1.0);
}
"""

FRAGMENT_SHADER = """
#version 330 core

#define fragCoord gl_FragCoord.xy

uniform vec2  iMouse;
uniform float iTime;
uniform vec2  iResolution;

out vec4 fragColor;

void main()
{
    // Set origin to center of the screen
    vec2 uv = fragCoord/iResolution.xy * 2.0 - 1.0;
    // Fix aspect ratio
    uv.x *= iResolution.x / iResolution.y;

    // Time varying pixel color (Copied from ShaderToy default scene)
    vec3 color = 0.5 + 0.5 * cos(iTime + uv.xyx + vec3(0.0, 2.0, 4.0));

    fragColor = vec4(color, 1.0);
}
"""


class Main(object):
    def __init__(self):
        pygame.init()
        self.resolution = 800, 600  
        pygame.display.set_mode(self.resolution, DOUBLEBUF | OPENGL)
        pygame.display.set_caption('PyShadeToy')        

        # Shaders
        self.vertex_shader = shaders.compileShader(VERTEX_SHADER, GL_VERTEX_SHADER)
        self.fragment_shader = shaders.compileShader(FRAGMENT_SHADER, GL_FRAGMENT_SHADER)

        # Shader program which hosts the vertex and fragment shader
        self.shader = shaders.compileProgram(self.vertex_shader, self.fragment_shader)

        # Uniform variables
        self.uni_mouse = glGetUniformLocation(self.shader, 'iMouse')
        self.uni_ticks = glGetUniformLocation(self.shader, 'iTime')

        glUseProgram(self.shader)   # Need to be enabled before sending uniform variables
        # Resolution doesn't change. Send it once
        glUniform2f(glGetUniformLocation(self.shader, 'iResolution'), *self.resolution)
        
        # Create the fullscreen quad for drawing
        self.vertices = array([-1.0, -1.0, 0.0,
                                1.0, -1.0, 0.0,
                                1.0,  1.0, 0.0,
                               -1.0,  1.0, 0.0], dtype='float32')

        self.vertexbuffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vertexbuffer)
        glBufferData(GL_ARRAY_BUFFER, self.vertices, GL_STATIC_DRAW)

        self.clock = pygame.time.Clock()

    def mainloop(self):
        while 1:
            delta = self.clock.tick(8192)

            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

            for event in pygame.event.get():
                if (event.type == QUIT) or (event.type == KEYUP and event.key == K_ESCAPE):
                    pygame.quit()
                    exitsystem()
                    
            glUseProgram(self.shader)

            glUniform2f(self.uni_mouse, *pygame.mouse.get_pos())
            glUniform1f(self.uni_ticks, pygame.time.get_ticks() / 1000.0)

            # Enable Vertex arrays
            glEnableVertexAttribArray(0)
            glBindBuffer(GL_ARRAY_BUFFER, self.vertexbuffer)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)

            glDrawArrays(GL_QUADS, 0, 4)

            glDisableVertexAttribArray(0) # Optional

            pygame.display.set_caption("FPS: {}".format(self.clock.get_fps()))
            pygame.display.flip()


if __name__ == '__main__':
    Main().mainloop()
