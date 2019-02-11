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

FRAGMENT_SHADER = """
#define NEAR_CLIPPING_PLANE 0.1
#define FAR_CLIPPING_PLANE 100.0
#define NUMBER_OF_MARCH_STEPS 40
#define EPSILON 0.01
#define DISTANCE_BIAS 0.7

// distance to sphere function (p is world position of the ray, s is sphere radius)
// from http://iquilezles.org/www/articles/distfunctions/distfunctions.htm
float sdSphere(vec3 p, float s)
{
	return length(p) - s;
}

float fmod(float a, float b)
{
    if(a<0.0)
    {
        return b - mod(abs(a), b);
    }
    return mod(a, b);
}
vec2 scene(vec3 position)
{
    /*
	This function generates a distance to the given position
	The distance is the closest point in the world to that position
	*/
    // to move the sphere one unit forward, we must subtract that translation from the world position
    vec3 translate = vec3(0.0, -0.5, 1.0);
    float distance = sdSphere(position - translate, 0.5);
	float materialID = 1.0;
    
    translate = vec3(0.0, 0.5, 1.0);
    // A power of raymarching is tiling, we can modify the position in any way we want
    // leaving the shape as is, creating various results
    // So let's tile in X with a sine wave offset in Y!
    vec3 sphere_pos = position - translate;
    // Because our sphere starts at 0 just tiling it would cut it in half, with
    // the other half on the other side of the tile. SO instead we offset it by 0.5
    // then tile it so it stays in tact and then do -0.5 to restore the original position.
    // When tiling by any tile size, offset your position by half the tile size like this!
    sphere_pos.x = fract(sphere_pos.x + 0.5) - 0.5; // fract() is mod(v, 1.0) or in mathemathical terms x % 1.0
    sphere_pos.z = fmod(sphere_pos.z + 1.0, 2.0) - 1.0; // example without fract
    // now let's animate the height!
    sphere_pos.y += sin(position.x + iGlobalTime) * 0.35; //add time to animate, multiply by samll number to reduce amplitude
    sphere_pos.y += cos(position.z + iGlobalTime);
    float distance2 = sdSphere(sphere_pos, 0.25);
	float materialID2 = 2.0; // the second sphere should have another colour
    
    // to combine two objects we use the minimum distance
    if(distance2 < distance)
    {
		distance = distance2;
        materialID = materialID2;
    }
    
    // we return a vec2 packing the distance and material of the closes object together
    return vec2(distance, materialID);
}


vec2 raymarch(vec3 position, vec3 direction)
{
    /*
	This function iteratively analyses the scene to approximate the closest ray-hit
	*/
    // We track how far we have moved so we can reconstruct the end-point later
    float total_distance = NEAR_CLIPPING_PLANE;
    for(int i = 0 ; i < NUMBER_OF_MARCH_STEPS ; ++i)
    {
        vec2 result = scene(position + direction * total_distance);
        // If our ray is very close to a surface we assume we hit it
        // and return it's material
        if(result.x < EPSILON)
        {
            return vec2(total_distance, result.y);
        }
        
        // Accumulate distance traveled
        // The result.x contains closest distance to the world
        // so we can be sure that if we move it that far we will not accidentally
        // end up inside an object. Due to imprecision we do increase the distance
        // by slightly less... it avoids normal errors especially.
        total_distance += result.x * DISTANCE_BIAS;
        
        // Stop if we are headed for infinity
        if(total_distance > FAR_CLIPPING_PLANE)
            break;
    }
    // By default we return no material and the furthest possible distance
    // We only reach this point if we didn't get close to a surface during the loop above
    return vec2(FAR_CLIPPING_PLANE, 0.0);
}

vec3 normal(vec3 ray_hit_position, float smoothness)
{	
    // From https://www.shadertoy.com/view/MdSGDW
	vec3 n;
	vec2 dn = vec2(smoothness, 0.0);
	n.x	= scene(ray_hit_position + dn.xyy).x - scene(ray_hit_position - dn.xyy).x;
	n.y	= scene(ray_hit_position + dn.yxy).x - scene(ray_hit_position - dn.yxy).x;
	n.z	= scene(ray_hit_position + dn.yyx).x - scene(ray_hit_position - dn.yyx).x;
	return normalize(n);
}


void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Given the pixel X, Y coordinate and the resolution we can get 0-1 UV space
	vec2 uv = fragCoord.xy / iResolution.xy;
    // Our rays should shoot left and right, so we move the 0-1 space and make it -1 to 1
    uv = uv * 2.0 - 1.0;
    // Last we deal with an aspect ratio in the window, to make sure our results are square
    // we must correct the X coordinate by the stretching of the resolution
    uv.x *= iResolution.x / iResolution.y;
    // Now to conver the UV to a ray we need a camera origin, like 0,0,0; and a direction
    // We can use the -1 to 1 UVs as ray X and Y, then we make sure the direction is length 1.0
    // by adding a Z component. Code blow is just an example:
    //float sqr_length = dot(uv, uv);
    //vec3 direction = vec3(uv, sqrt(1.0 - sqr_length));
    
    // a shorter and easier way is to create a vec3 and normalise it, 
    // we can manually change the Z component to change the final FOV; 
    // smaller Z is bigger FOV
    vec3 direction = normalize(vec3(uv, 2.5));
    // if you rotate the direction with a rotatin matrix you can turn the camera too!
    
    vec3 camera_origin = vec3(0.0, 0.0, -2.5); // you can move the camera here
    
    vec2 result = raymarch(camera_origin, direction); // this raymarches the scene
    
    // arbitrary fog to hide artifacts near the far plane
    // 1.0 / distance results in a nice fog that starts white
    // but if distance is 0 
    float fog = pow(1.0 / (1.0 + result.x), 0.45);
    
    // now let's pick a color
    vec3 materialColor = vec3(0.0, 0.0, 0.0);
    if(result.y == 1.0)
    {
        materialColor = vec3(1.0, 0.25, 0.1);
    }
    if(result.y == 2.0)
    {
       	materialColor = vec3(0.7, 0.7, 0.7);
    }
    
    // We can reconstruct the intersection point using the distance and original ray
    vec3 intersection = camera_origin + direction * result.x;
    
    // The normals can be retrieved in a fast way
    // by taking samples close to the end-result sample
    // their resulting distances to the world are used to see how the surface curves in 3D
    // This math I always steal from somewhere ;)
    vec3 nrml = normal(intersection, 0.01);
    
    // Lambert lighting is the dot product of a directional light and the normal
    vec3 light_dir = normalize(vec3(0.0, 1.0, 0.0));
   	float diffuse = dot(light_dir, nrml);
    // Wrap the lighting around
    // https://developer.valvesoftware.com/wiki/Half_Lambert
    diffuse = diffuse * 0.5 + 0.5;
    // For real diffuse, use this instead (to avoid negative light)
    //diffuse = max(0.0, diffuse);
    
    // Combine ambient light and diffuse lit directional light
    vec3 light_color = vec3(1.4, 1.2, 0.7);
    vec3 ambient_color = vec3(0.2, 0.45, 0.6);
    vec3 diffuseLit = materialColor * (diffuse * light_color + ambient_color);
	fragColor = vec4(diffuseLit, 1.0) * fog; /* applying the fog last */
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

        glUseProgram(self.shader)
        # Resolution doesn't change. Send it once
        self.uni_resolution = glGetUniformLocation(self.shader, 'iResolution')
        glUniform2f(self.uni_resolution, *self.resolution)
        
        # Create Vertex Buffer
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

            glDisableVertexAttribArray(0)

            pygame.display.set_caption("FPS: {}".format(self.clock.get_fps()))
            pygame.display.flip()


if __name__ == '__main__':
    Main().mainloop()
