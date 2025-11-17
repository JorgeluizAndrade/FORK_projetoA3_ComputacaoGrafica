#version 410 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;

// Matrizes para transformar o 3D em 2D na tela
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 u_light_space_matrix; // Matriz da luz

// Saída para o Fragment Shader
out vec3 v_normal;
out vec3 v_world_pos; // Posição no mundo (para iluminação)
out vec4 v_frag_pos_light_space; // Posição na visão da luz

void main()
{
    // Calcular posição no espaço do mundo
    vec4 world_pos_4 = model * vec4(in_position, 1.0);
    v_world_pos = world_pos_4.xyz;
    v_normal = mat3(model) * in_normal;
    
    // Calcular onde este vértice está na "tela" do sol
    v_frag_pos_light_space = u_light_space_matrix * world_pos_4;

    // Posição final na tela
    gl_Position = projection * view * world_pos_4;
}