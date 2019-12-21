# Note: There was old version which was done wrongly long time ago
#       Ive noticed a few people using this lately and wanted to fix this
#       
#
#       This is the fixed version where both "vao" and "vbo" are created
#       Everything else is the same


from __future__ import division
import pygame
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.GLU import *

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

# https://www.iquilezles.org/www/articles/distfunctions/distfunctions.htm
# https://github.com/PistonDevelopers/shaders/wiki/Some-useful-GLSL-functions

FRAGMENT_SHADER = """
#version 330 core

#define fragCoord gl_FragCoord.xy

uniform vec2  iMouse;
uniform float iTime;
uniform vec2  iResolution;

out vec4 fragColor;

float sdSphere(vec3 p, float r)
{
  return length(p) - r;
}


float map_the_world(in vec3 pos)
{
    float displacement = sin(abs(4.0 * cos(iTime)) * pos.x) *
                         sin(abs(4.0 * sin(iTime)) * pos.y) *
                         sin(4.0                   * pos.z) *
                        (0.1 + abs(0.1 * sin(iTime * 2.0)));
    float sphere_0 = sdSphere(pos, 2.5) + displacement;

    return sphere_0;
}


vec3 calculate_normal(in vec3 pos)
{
    const vec3 small_step = vec3(0.001, 0.0, 0.0);

    float gradient_x = map_the_world(pos + small_step.xyy) - map_the_world(pos - small_step.xyy);
    float gradient_y = map_the_world(pos + small_step.yxy) - map_the_world(pos - small_step.yxy);
    float gradient_z = map_the_world(pos + small_step.yyx) - map_the_world(pos - small_step.yyx);

    vec3 normal = vec3(gradient_x, gradient_y, gradient_z);

    return normalize(normal);
}


vec3 ray_march(in vec3 ro, in vec3 rd)
{
    float total_distance_traveled = 0.0;
    const int NUMBER_OF_STEPS = 128;

    const float MINIMUM_HIT_DISTANCE = 0.001;
    const float MAXIMUM_TRACE_DISTANCE = 512.0;
    const float AMBIENT = 0.2;

    for (int i = 0; i < NUMBER_OF_STEPS; ++i)
    {
        vec3 current_position = ro + total_distance_traveled * rd;

        float distance_to_closest = map_the_world(current_position);

        if (distance_to_closest < MINIMUM_HIT_DISTANCE) 
        {
            vec3 normal = calculate_normal(current_position);
            vec3 light_position = vec3(-iMouse.x, iMouse.y, 4.0);
            vec3 direction_to_light = normalize(current_position - light_position);

            float diffuse_intensity = max(AMBIENT, pow(dot(normal, direction_to_light), 16.0));

            return vec3(1.0, 0.0, 0.0) * diffuse_intensity;
        }

        if (total_distance_traveled > MAXIMUM_TRACE_DISTANCE){
            break;
        }
        total_distance_traveled += distance_to_closest;
    }
    return vec3(0.0);
}


void main()
{
    vec2 uv = fragCoord / iResolution.xy * 2.0 - 1.0;
    uv.x *= iResolution.x / iResolution.y;

    vec3 camera_position = vec3(0.0, 0.0, -5.0);
    vec3 ray_origin = camera_position;
    vec3 ray_direction = vec3(uv, 1.0);

    vec3 result = ray_march(ray_origin, ray_direction);

    fragColor = vec4(result, 1.0);
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
        self.shader = shaders.compileProgram(self.vertex_shader, self.fragment_shader)

        # Uniform variables
        self.uni_mouse = glGetUniformLocation(self.shader, 'iMouse')
        self.uni_ticks = glGetUniformLocation(self.shader, 'iTime')

        glUseProgram(self.shader)   # Shader program needs to be active if you send uniform variables
        # Resolution doesn't change. Send it once
        self.uni_resolution = glGetUniformLocation(self.shader, 'iResolution')
        glUniform2f(self.uni_resolution, *self.resolution)
        
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

                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 4:
                        pass
            
            glUseProgram(self.shader)

            # Map mouse coordinates between -1 and 1 range
            mx, my = pygame.mouse.get_pos()
            mx = (1.0 / self.resolution[0] * mx) * 2.0 - 1.0
            my = (1.0 / self.resolution[1] * my) * 2.0 - 1.0
            
            glUniform2f(self.uni_mouse, mx, my)
            glUniform1f(self.uni_ticks, pygame.time.get_ticks() / 1000.0)

            # Bind the vao (which stores the VBO with all the vertices)
            glBindVertexArray(self.vao)
            glDrawArrays(GL_QUADS, 0, 4)

            pygame.display.set_caption("FPS: {}".format(self.clock.get_fps()))
            pygame.display.flip()


if __name__ == '__main__':
    Main().mainloop()
