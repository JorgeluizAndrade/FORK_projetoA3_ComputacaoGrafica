#version 410 core
layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;
layout (location = 2) in vec2 in_tex_coords;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 u_light_space_matrix; // Sombra (Fase 2)

out vec3 v_normal;
out vec2 v_tex_coords;
out vec4 v_frag_pos_light_space;

void main()
{
    vec4 world_pos = model * vec4(in_position, 1.0);
    v_normal = mat3(model) * in_normal;
    v_tex_coords = in_tex_coords;
    
    // Sombra
    v_frag_pos_light_space = u_light_space_matrix * world_pos;

    gl_Position = projection * view * world_pos;
}