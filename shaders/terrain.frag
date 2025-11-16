#version 410 core

out vec4 out_color;

// Entrada do Vertex Shader
in vec3 v_normal;
in vec3 v_world_pos;

// Uniforms de Iluminação
uniform vec3 u_sun_direction;
uniform vec3 u_sun_color;
uniform vec3 u_ambient_color;

// Cor base do terreno (verde)
const vec3 TERRAIN_COLOR = vec3(0.3, 0.6, 0.2);

void main()
{
    // Preparar vetores
    vec3 N = normalize(v_normal);
    vec3 L = normalize(u_sun_direction); // Luz já é uma direção

    // Calcular intensidade difusa (Blinn-Phong)
    float diffuse_intensity = max(0.0, dot(N, L));

    // Quantizar (Degraus)
    float toon_factor;
    if (diffuse_intensity > 0.9) {
        toon_factor = 1.0; // Destaque
    } else if (diffuse_intensity > 0.6) {
        toon_factor = 0.7; // Meio-tom
    } else if (diffuse_intensity > 0.3) {
        toon_factor = 0.4; // Sombra clara
    } else {
        toon_factor = 0.1; // Sombra escura
    }

    // Calcular cor final 
    vec3 lighting = (u_ambient_color + toon_factor * u_sun_color);
    vec3 final_color = TERRAIN_COLOR * lighting;
    
    out_color = vec4(final_color, 1.0);
}