# Note: There was old version which was done wrongly long time ago
#       Ive noticed a few people using this lately and wanted to fix this
#       
#
#       This is the fixed version where both "vao" and "vbo" are created
#       Everything else is the same


from __future__ import division
import pygame
from pygame.locals import *

import ctypes as ct
from OpenGL.GL import * 
from OpenGL.GL import shaders
#from OpenGL.GLU import *

from sys import exit as exitsystem

from numpy import array


VERTEX_SHADER_FIRST = """
#version 330 core
layout(location = 0) in vec3 vPos;
void main()
{
    gl_Position = vec4(vPos, 1.0);
}
"""

FRAGMENT_SHADER_FIRST = """
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


VERTEX_SHADER_SECOND = """
#version 330 core
layout(location = 0) in vec3 vPos;
layout(location = 1) in vec2 texCoords;

out vec2 texcoords;

void main()
{
    gl_Position = vec4(vPos, 1.0);
    texcoords = texCoords;
}
"""

# We can read the texture now and modify it from the first pass
# I decided to multiply the texture coordinates to provide multiple smaller screens
FRAGMENT_SHADER_SECOND = """
#version 330 core
#define fragCoord gl_FragCoord.xy

out vec4 fragColor;
in vec2 texcoords;

uniform sampler2D tex;

void main()
{
    vec4 color = texture(tex, texcoords * 4.0);
    fragColor = color;
}
"""


class Main(object):
    def __init__(self):
        pygame.init()
        self.resolution = 800, 600  
        pygame.display.set_mode(self.resolution, DOUBLEBUF | OPENGL)
        pygame.display.set_caption('PyShadeToy')        

        # ------------------ Build the first shader ------------------ 
        # Shaders
        self.vertex_shader = shaders.compileShader(VERTEX_SHADER_FIRST, GL_VERTEX_SHADER)
        self.fragment_shader = shaders.compileShader(FRAGMENT_SHADER_FIRST, GL_FRAGMENT_SHADER)

        # Shader program which hosts the vertex and fragment shader
        self.shader = shaders.compileProgram(self.vertex_shader, self.fragment_shader)

        # Get the uniform locations
        self.uni_mouse = glGetUniformLocation(self.shader, 'iMouse')
        self.uni_ticks = glGetUniformLocation(self.shader, 'iTime')

        glUseProgram(self.shader)   # Need to be enabled before sending uniform variables
        # Resolution doesn't change. Send it once
        glUniform2f(glGetUniformLocation(self.shader, 'iResolution'), *self.resolution)


        #  ------------------ Build the second shader  ------------------ 
        self.vertex_shader2 = shaders.compileShader(VERTEX_SHADER_SECOND, GL_VERTEX_SHADER)
        self.fragment_shader2 = shaders.compileShader(FRAGMENT_SHADER_SECOND, GL_FRAGMENT_SHADER)

        # Shader program which hosts the vertex and fragment shader
        self.shader2 = shaders.compileProgram(self.vertex_shader2, self.fragment_shader2)


        
        #  ------------------ Build the first vao  ------------------ 
        # Create the fullscreen quad for drawing
        self.vertices = array([-1.0, -1.0, 0.0,
                                1.0, -1.0, 0.0,
                                1.0,  1.0, 0.0,
                               -1.0,  1.0, 0.0], dtype='float32')

        # Generate VAO
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        # Generate VBO which is stored in the VAO state
        self.vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vertices, GL_STATIC_DRAW)

        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)



        #  ------------------Build the second vao  ------------------ 
        # Create the fullscreen quad for drawing (This time we need texture coordinates too)
        self.vertices2 = array([-1.0, -1.0, 0.0,  0.0, 0.0, 
                                 1.0, -1.0, 0.0,  1.0, 0.0,
                                 1.0,  1.0, 0.0,  1.0, 1.0,
                                -1.0,  1.0, 0.0,  0.0, 1.0], dtype='float32')

        # Generate VAO
        self.vao2 = glGenVertexArrays(1)
        glBindVertexArray(self.vao2)

        # Generate VBO which is stored in the VAO state
        self.vbo2 = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo2)
        glBufferData(GL_ARRAY_BUFFER, self.vertices2, GL_STATIC_DRAW)

        # Note: offsets are calculated with float assumed to be 4 bytes long and stride consist of
        # stride = vec3 position + vec2 texture coordinates
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 4 * 5, None)

        glEnableVertexAttribArray(1)
        # The last is the offset which tells the OpenGL where the texture coordinates begin
        # from the stride
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 4 * 5, ctypes.cast(4 * 3, ctypes.c_void_p))
        

        
        #  ------------------ Generate framebuffer  ------------------  
        self.frame, self.texture = self.genFrameBuffer()

        
        self.clock = pygame.time.Clock()

    
    def genFrameBuffer(self):
        """
            Generate Framebuffer and attach color texture to it

            return -> complete framebuffer and texture
        """
        # Create framebuffer
        frame = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, frame)

        # Create the texture and attach it
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)

        # Set the texture parameters
        w, h = self.resolution
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR) 

        # Attach it to the framebuffer
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0)

        # Note: There would depth and stencil attachment here but since we are doing
        # fullscreen quad without 3d models, depth texture is not needed
        
        # Make sure the frame buffer is complete
        if glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE:
            print "Success!"

        # Unbind it
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        return frame, texture

    
    def mainloop(self):
        while 1:
            delta = self.clock.tick(8192)

            for event in pygame.event.get():
                if (event.type == QUIT) or (event.type == KEYUP and event.key == K_ESCAPE):
                    pygame.quit()
                    exitsystem()


            #  ------------------ first pass  ------------------ 
            glBindFramebuffer(GL_FRAMEBUFFER, self.frame)
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)
            
            glUseProgram(self.shader)

            # Send uniform values
            glUniform2f(self.uni_mouse, *pygame.mouse.get_pos())
            glUniform1f(self.uni_ticks, pygame.time.get_ticks() / 1000.0)

            # Bind the vao (which stores the VBO with all the vertices)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_QUADS, 0, 4)

            # Lets go back to the default screen buffer
            glBindFramebuffer(GL_FRAMEBUFFER, 0)


            #  ------------------ Second pass  ------------------ 
            glClearColor(0.0, 0.0, 0.0, 1.0)
            glClear(GL_COLOR_BUFFER_BIT)

            glUseProgram(self.shader2)
            # Bind the texture we rendered to from the first pass
            glBindTexture(GL_TEXTURE_2D, self.texture)

            # Draw the fullscreen quad using the texture
            glBindVertexArray(self.vao2)
            glDrawArrays(GL_QUADS, 0, 4)


            
            pygame.display.set_caption("FPS: {}".format(self.clock.get_fps()))
            pygame.display.flip()


if __name__ == '__main__':
    Main().mainloop()
