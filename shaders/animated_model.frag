#version 410 core
out vec4 out_color;

in vec3 v_normal;
in vec2 v_tex_coords;
in vec4 v_frag_pos_light_space;

uniform vec3 u_sun_direction;
uniform vec3 u_sun_color;
uniform vec3 u_ambient_color;
uniform sampler2D u_shadow_map;

// Cor provisória do personagem (Cinza)
const vec3 CHAR_COLOR = vec3(0.7, 0.7, 0.7);

// Função de sombra (Mesma do terreno)
float calculate_shadow(vec4 frag_pos_light_space, vec3 normal, vec3 light_dir)
{
    vec3 proj_coords = frag_pos_light_space.xyz / frag_pos_light_space.w;
    proj_coords = proj_coords * 0.5 + 0.5;
    if(proj_coords.z > 1.0) return 0.0;
    float closest_depth = texture(u_shadow_map, proj_coords.xy).r; 
    float current_depth = proj_coords.z;
    float bias = max(0.005 * (1.0 - dot(normal, light_dir)), 0.001);  
    float shadow = current_depth - bias > closest_depth ? 1.0 : 0.0;
    return shadow;
}

void main()
{
    vec3 N = normalize(v_normal);
    vec3 L = normalize(u_sun_direction);
    
    // Toon Shading
    float diffuse_intensity = max(0.0, dot(N, L));
    float toon_factor = diffuse_intensity > 0.5 ? 1.0 : 0.3; // 2 Níveis simples

    float shadow = calculate_shadow(v_frag_pos_light_space, N, L);
    vec3 lighting = u_ambient_color + (1.0 - shadow) * (toon_factor * u_sun_color);
    
    out_color = vec4(CHAR_COLOR * lighting, 1.0);
}