#version 410 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
layout (location = 2) in vec2 aTexCoords;

// MUDANÇA: Agora recebemos como vec4 (floats), não ivec4
layout (location = 3) in vec4 aBoneIDs; 
layout (location = 4) in vec4 aWeights;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 u_light_space_matrix;

const int MAX_BONES = 100;
uniform mat4 u_finalBones[MAX_BONES];

out vec3 v_frag_pos;
out vec3 v_normal;
out vec2 v_tex_coords;
out vec4 v_frag_pos_light_space;

void main()
{
    mat4 BoneTransform = mat4(0.0);
    float totalWeight = 0.0;

    // Convertemos float para int manualmente aqui
    int id0 = int(aBoneIDs.x);
    int id1 = int(aBoneIDs.y);
    int id2 = int(aBoneIDs.z);
    int id3 = int(aBoneIDs.w);

    // Osso 1
    if (id0 >= 0 && id0 < MAX_BONES) { 
        BoneTransform += u_finalBones[id0] * aWeights.x; 
        totalWeight += aWeights.x; 
    }
    // Osso 2
    if (id1 >= 0 && id1 < MAX_BONES) { 
        BoneTransform += u_finalBones[id1] * aWeights.y; 
        totalWeight += aWeights.y; 
    }
    // Osso 3
    if (id2 >= 0 && id2 < MAX_BONES) { 
        BoneTransform += u_finalBones[id2] * aWeights.z; 
        totalWeight += aWeights.z; 
    }
    // Osso 4
    if (id3 >= 0 && id3 < MAX_BONES) { 
        BoneTransform += u_finalBones[id3] * aWeights.w; 
        totalWeight += aWeights.w; 
    }

    // Se for estático ou erro de peso, usa identidade
    if (totalWeight < 0.001) {
        BoneTransform = mat4(1.0);
    }

    vec4 animatedPos = BoneTransform * vec4(aPos, 1.0);
    vec4 animatedNormal = BoneTransform * vec4(aNormal, 0.0);

    v_frag_pos = vec3(model * animatedPos);
    v_normal = normalize(mat3(transpose(inverse(model))) * vec3(animatedNormal));
    v_tex_coords = aTexCoords;
    v_frag_pos_light_space = u_light_space_matrix * vec4(v_frag_pos, 1.0);

    gl_Position = projection * view * vec4(v_frag_pos, 1.0);
}