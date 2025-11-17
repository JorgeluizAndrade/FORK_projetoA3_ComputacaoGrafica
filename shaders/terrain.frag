#version 410 core

out vec4 out_color;

// Entrada do Vertex Shader
in vec3 v_normal;
in vec3 v_world_pos;
in vec4 v_frag_pos_light_space; // Recebido do Vertex Shader

// Uniforms de Iluminação
uniform vec3 u_sun_direction;
uniform vec3 u_sun_color;
uniform vec3 u_ambient_color;
uniform sampler2D u_shadow_map; // O Mapa de Sombr

// Cor base do terreno (verde)
const vec3 TERRAIN_COLOR = vec3(0.3, 0.6, 0.2);

float calculate_shadow(vec4 frag_pos_light_space, vec3 normal, vec3 light_dir)
{
    // Divisão Perspectiva (transforma para coordenadas normalizadas -1 a 1)
    vec3 proj_coords = frag_pos_light_space.xyz / frag_pos_light_space.w;
    
    // Transformar para range [0, 1] (para ler a textura)
    proj_coords = proj_coords * 0.5 + 0.5;
    
    // Se estiver fora do mapa de sombra, não tem sombra
    if(proj_coords.z > 1.0)
        return 0.0;

    // Ler a profundidade mais próxima (do mapa)
    float closest_depth = texture(u_shadow_map, proj_coords.xy).r; 
    
    // Ler a profundidade atual do fragmento
    float current_depth = proj_coords.z;

    // Viés (Bias) para evitar "Shadow Acne" (listras pretas feias)
    // Ajustamos o viés com base na inclinação da luz
    float bias = max(0.005 * (1.0 - dot(normal, light_dir)), 0.001);  

    // Teste de Sombra (PCF Simples - Opcional, aqui é sombra dura)
    float shadow = current_depth - bias > closest_depth ? 1.0 : 0.0;
    
    return shadow;
}

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

    // CÁLCULO DA SOMBRA
    float shadow = calculate_shadow(v_frag_pos_light_space, N, L);

    // A sombra afeta apenas o componente difuso (Sol), não o ambiente
    vec3 lighting = u_ambient_color + (1.0 - shadow) * (toon_factor * u_sun_color);
    
    out_color = vec4(TERRAIN_COLOR * lighting, 1.0);
}