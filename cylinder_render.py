import sys, os, math
from PIL import Image
import numpy as np
from stl import mesh

def generate_unified_litho(job_path, socket_type, shape, sides, img_count):
    # Load and prepare images
    imgs = []
    for i in range(img_count):
        img = Image.open(os.path.join(job_path, f"input_{i}.png")).convert('L')
        img = img.resize((600, 600), Image.Resampling.LANCZOS)
        imgs.append(np.flipud(np.asarray(img)))

    rows, cols = 600, 600
    radius, height, min_t, max_t = 60, 120, 0.8, 3.0
    vertices, faces = [], []

    iterations_per_photo = int(sides / img_count)
    cols_per_side = cols / sides

    # 1. Generate Body
    for r in range(rows):
        z = (r / (rows - 1)) * height
        img_y = int((r / (rows - 1)) * 599)
        
        for c in range(cols):
            angle = (c / cols) * 2 * math.pi
            side_idx = int(c / cols_per_side)
            if side_idx >= sides: side_idx = sides - 1
            
            img_idx = int(side_idx / iterations_per_photo)
            if img_idx >= img_count: img_idx = img_count - 1
            
            local_x_norm = (c % cols_per_side) / cols_per_side
            img_x = int(local_x_norm * 599)

            # Geometry Radius Calculation
            current_radius = radius
            if shape != "Cylinder":
                segment_angle = (2 * math.pi) / sides
                face_center_angle = (side_idx * segment_angle) + (segment_angle / 2)
                current_radius = radius / math.cos(angle - face_center_angle)

            pixel_val = imgs[img_idx][img_y, img_x]
            t = min_t + (1.0 - pixel_val/255.0) * (max_t - min_t)
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            
            vertices.append([(current_radius + t) * cos_a, (current_radius + t) * sin_a, z])
            vertices.append([current_radius * cos_a, current_radius * sin_a, z])

    v_row = cols * 2
    for r in range(rows - 1):
        for c in range(cols):
            cn = (c + 1) % cols
            o1, i1, o2, i2 = r*v_row+c*2, r*v_row+c*2+1, r*v_row+cn*2, r*v_row+cn*2+1
            o3, i3, o4, i4 = (r+1)*v_row+c*2, (r+1)*v_row+c*2+1, (r+1)*v_row+cn*2, (r+1)*v_row+cn*2+1
            faces.extend([[o1, o2, o3], [o2, o4, o3], [i1, i3, i2], [i2, i3, i4]])

    # 2. Add Parametric Mounting Plate
    # Standard puck diameter for many LED bases is ~85mm (42.5 radius), hole at ~40mm
    hole_r = 20 if socket_type == "E26" else (10 if socket_type == "E12" else 42.5)
    plate_z_pos = (height - 3.5) if socket_type != "Base" else 0
    plate_thickness = 3.5
    
    h_idx = len(vertices)
    for c in range(cols):
        a = (c / cols) * 2 * math.pi
        vertices.append([hole_r * math.cos(a), hole_r * math.sin(a), plate_z_pos])
        vertices.append([hole_r * math.cos(a), hole_r * math.sin(a), plate_z_pos + plate_thickness])

    # Connect Plate to Cylinder Walls
    wall_ref_row = (rows - 1) if socket_type != "Base" else 0
    wall_start = wall_ref_row * v_row
    for c in range(cols):
        cn = (c + 1) % cols
        w1, w2 = wall_start + c*2, wall_start + cn*2
        hb1, hb2 = h_idx + c*2, h_idx + cn*2
        faces.extend([[w1, hb1, w2], [hb1, hb2, w2]])

    # 3. Add Solid Top/Bottom Seal (Opposite of the mount)
    seal_z = 0 if socket_type != "Base" else height
    seal_start = 0 if socket_type != "Base" else (rows-1)*v_row
    s_idx = len(vertices)
    for c in range(cols):
        a = (c / cols) * 2 * math.pi
        vertices.append([5 * math.cos(a), 5 * math.sin(a), seal_z]) # 10mm center vent
        
        cn = (c + 1) % cols
        # Connect inner/outer walls to center hole
        o1, i1, o2, i2 = seal_start+c*2, seal_start+c*2+1, seal_start+cn*2, seal_start+cn*2+1
        sc1, sc2 = s_idx+c, s_idx+cn
        faces.extend([[o1, o2, i1], [o2, i2, i1]]) # Outer Rim Seal
        faces.extend([[i1, i2, sc1], [i2, sc2, sc1]]) # Center Cap

    out_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3): out_mesh.vectors[i][j] = vertices[f[j]]
    out_mesh.save(os.path.join(job_path, "final.stl"))

if __name__ == "__main__":
    generate_unified_litho(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
