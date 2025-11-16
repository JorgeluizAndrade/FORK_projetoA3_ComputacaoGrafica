#version 410 core

layout (location = 0) in vec3 in_position;
layout (location = 1) in vec3 in_normal;

// Matrizes para transformar o 3D em 2D na tela
uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

// Saída para o Fragment Shader
out vec3 v_normal;
out vec3 v_world_pos; // Posição no mundo (para iluminação)

void main()
{
    // Calcular posição no espaço do mundo
    vec4 world_pos_4 = model * vec4(in_position, 1.0);
    v_world_pos = world_pos_4.xyz;
    
    // Calcular normal no espaço do mundo (sem translação) Usamos a inversa transposta da matriz model, mas como model é identidade,
    v_normal = mat3(model) * in_normal;

    // Posição final na tela
    gl_Position = projection * view * world_pos_4;
}