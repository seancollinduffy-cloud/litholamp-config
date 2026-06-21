import sys, os, math
from PIL import Image
import numpy as np
from stl import mesh

def generate_unified_litho(job_path, socket_type, shape, sides, img_count, height_val=120.0, diameter_val=100.0, thickness_val=3.0):
    # Load and prepare images
    imgs = []
    for i in range(img_count):
        img = Image.open(os.path.join(job_path, f"input_{i}.png")).convert('L')
        
        # We need to scale the image to fit the aspect ratio of the generated cylinder
        if shape == "Cylinder" or shape == "Tiffany":
            # If Tiffany and portrait, tile the image 3 times horizontally
            if shape == "Tiffany" and img.width < img.height:
                padding = int(img.width * 0.1) # 10% padding
                new_w = (img.width * 3) + (padding * 3)
                tiled = Image.new('L', (new_w, img.height), color=255)
                tiled.paste(img, (padding // 2, 0))
                tiled.paste(img, (img.width + int(padding * 1.5), 0))
                tiled.paste(img, (img.width * 2 + int(padding * 2.5), 0))
                img = tiled

            cyl_aspect = ((diameter_val * math.pi) / img_count) / height_val
            img_aspect = img.width / img.height
            if img_aspect > cyl_aspect:
                new_h = int(img.width / cyl_aspect)
                padded = Image.new('L', (img.width, new_h), color=255)
                padded.paste(img, (0, (new_h - img.height) // 2))
                img = padded
            else:
                new_w = int(img.height * cyl_aspect)
                padded = Image.new('L', (new_w, img.height), color=255)
                padded.paste(img, ((new_w - img.width) // 2, 0))
                img = padded
            img = img.resize((600, 600), Image.Resampling.LANCZOS)
        else:
            # Polygons get a precise 5mm physical frame around the image
            face_width = diameter_val * math.tan(math.pi / sides)
            margin_x_px = int((5.0 / face_width) * 600)
            margin_y_px = int((5.0 / height_val) * 600)
            
            target_w = 600 - 2 * margin_x_px
            target_h = 600 - 2 * margin_y_px
            
            if target_w > 0 and target_h > 0:
                resized = img.resize((target_w, target_h), Image.Resampling.LANCZOS)
                padded = Image.new('L', (600, 600), color=255)
                padded.paste(resized, (margin_x_px, margin_y_px))
                img = padded
            else:
                img = img.resize((600, 600), Image.Resampling.LANCZOS)
        imgs.append(np.flipud(np.asarray(img)))

    rows, cols = 600, 600
    radius, height, min_t, max_t = diameter_val / 2.0, height_val, 0.8, thickness_val
    top_radius = radius * 0.6 if shape == "Tiffany" else radius
    
    # We want a 4mm wide slit on the very top edge at the back.
    # For Cylinder/Tiffany, the back is at PI.
    # For Square, the back face center is at 3*PI/4 (because it gets rotated by PI/4 later).
    slit_center = 3 * math.pi / 4 if shape == "Square" else math.pi
    slit_width_mm = 4.0
    slit_width_cols = max(2, int((slit_width_mm / (2 * math.pi * top_radius)) * cols))
    slit_half_angle = (slit_width_cols // 2) / cols * 2 * math.pi
    slit_start_angle = slit_center - slit_half_angle
    slit_end_angle = slit_center + slit_half_angle
    
    vertices, faces = [], []

    cols_per_image = cols / img_count
    iterations_per_photo = int(sides / img_count) if sides > 0 else 1

    # 1. Generate Body
    for r in range(rows):
        z = (r / (rows - 1)) * height
        img_y = int((r / (rows - 1)) * 599)
        
        for c in range(cols):
            angle = (c / cols) * 2 * math.pi
            
            if shape == "Cylinder" or shape == "Tiffany":
                shifted_c = (c + cols // 2) % cols
                img_idx = int(shifted_c / cols_per_image)
                if img_idx >= img_count: img_idx = img_count - 1
                local_x_norm = (shifted_c % cols_per_image) / cols_per_image
                current_radius = radius
                if shape == "Tiffany":
                    z_norm = z / height
                    scale = 1.0 - z_norm * 0.4
                    current_radius = radius * scale
                    # Conical undistortion: stretch the image at the top so it maintains a perfectly rectangular physical shape
                    local_x_norm = 0.5 + (local_x_norm - 0.5) * scale
            else:
                segment_angle = (2 * math.pi) / sides
                side_idx = int(angle / segment_angle)
                if side_idx >= sides: side_idx = sides - 1
                face_center_angle = side_idx * segment_angle + segment_angle / 2
                current_radius = radius / math.cos(angle - face_center_angle)
                
                # For polygons, map one image per flat face
                img_idx = int(side_idx / iterations_per_photo)
                if img_idx >= img_count: img_idx = img_count - 1
                
                # True linear projection onto the flat face
                half_width = radius * math.tan(math.pi / sides)
                dist_along_face = radius * math.tan(angle - face_center_angle)
                local_x_norm = (dist_along_face + half_width) / (2 * half_width)
            
            # Clamp local_x_norm just in case of float inaccuracies
            local_x_norm = max(0.0, min(1.0, local_x_norm))
            img_x = int(local_x_norm * 599)

            pixel_val = imgs[img_idx][img_y, img_x]
            
            # Add 1-inch (25.4mm) solid borders to Tiffany top and bottom
            if shape == "Tiffany":
                if z < 25.4 or z > height - 25.4:
                    pixel_val = 0 # 0 pixel value = maximum thickness (solid)
            
            t = min_t + (1.0 - pixel_val/255.0) * (max_t - min_t)
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            
            # Top External Edge Notch (Suction Break / Air Inlet)
            # We print upside down, so the "top" of the lamp is actually the bottom of the cup!
            # Compress z in the slit region to form a notch without self-intersecting geometry
            adjusted_z = z
            if slit_start_angle <= angle <= slit_end_angle:
                if z > height - 2.0:
                    adjusted_z = height - 2.0
                
            # Interior Lithophane: Outer wall is a smooth shape, inner wall is bumpy
            outer_r = current_radius + max_t
            inner_r = current_radius + max_t - t
            
            vertices.append([outer_r * cos_a, outer_r * sin_a, adjusted_z])
            vertices.append([inner_r * cos_a, inner_r * sin_a, adjusted_z])

    v_row = cols * 2
    for r in range(rows - 1):
        for c in range(cols):
            cn = (c + 1) % cols
            o1, i1, o2, i2 = r*v_row+c*2, r*v_row+c*2+1, r*v_row+cn*2, r*v_row+cn*2+1
            o3, i3, o4, i4 = (r+1)*v_row+c*2, (r+1)*v_row+c*2+1, (r+1)*v_row+cn*2, (r+1)*v_row+cn*2+1
            faces.extend([[o1, o2, o3], [o2, o4, o3], [i1, i3, i2], [i2, i3, i4]])

    # Parameters for CSG additions
    hole_r = 20 if socket_type == "E26" else (10 if socket_type == "E12" else 42.5)
    plate_z_pos = 0
    plate_thickness = 3.5

    # 2. Add Top Rim Seal & Bottom Rim Seal (Open Cylinder Ends)
    seal_start = (rows-1)*v_row
    wall_start = 0
    for c in range(cols):
        cn = (c + 1) % cols
        # Top Rim
        o1, i1, o2, i2 = seal_start+c*2, seal_start+c*2+1, seal_start+cn*2, seal_start+cn*2+1
        faces.extend([[o1, o2, i1], [o2, i2, i1]])
        # Bottom Rim
        b_o1, b_i1, b_o2, b_i2 = wall_start+c*2, wall_start+c*2+1, wall_start+cn*2, wall_start+cn*2+1
        faces.extend([[b_o1, b_i1, b_o2], [b_o2, b_i1, b_i2]])

    out_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3): out_mesh.vectors[i][j] = vertices[f[j]]

    meshes_to_concat = [out_mesh]

    # Helper: Manifold Annular Sector (Pie Slice) generator for solid roofs/floors with holes
    def create_annular_sector(r_out, r_in, z_out, z_in, a1, a2, t, segs=30, match_shape=False):
        verts = []
        faces = []
        for i in range(segs + 1):
            a = a1 + (a2 - a1) * (i / segs)
            
            current_r_out = r_out
            if match_shape and shape != "Cylinder" and shape != "Tiffany":
                segment_angle = (2 * math.pi) / sides
                side_idx = int(a / segment_angle)
                if side_idx >= sides: side_idx = sides - 1
                face_center_angle = side_idx * segment_angle + segment_angle / 2
                # Perfectly match the wall's outer surface equation + 0.5mm overlap
                current_r_out = (top_radius / math.cos(a - face_center_angle)) + max_t + 0.5
                
            verts.append([r_in * math.cos(a), r_in * math.sin(a), z_in])       # 0: IB
            verts.append([r_in * math.cos(a), r_in * math.sin(a), z_in + t])   # 1: IT
            verts.append([current_r_out * math.cos(a), current_r_out * math.sin(a), z_out])    # 2: OB
            verts.append([current_r_out * math.cos(a), current_r_out * math.sin(a), z_out + t])# 3: OT
            
        for i in range(segs):
            c = i * 4
            cn = (i + 1) * 4
            ib1, it1, ob1, ot1 = c, c+1, c+2, c+3
            ib2, it2, ob2, ot2 = cn, cn+1, cn+2, cn+3
            
            # Top (+Z)
            faces.extend([[ot1, ot2, it1], [ot2, it2, it1]])
            # Bottom (-Z)
            faces.extend([[ob1, ib1, ob2], [ib1, ib2, ob2]])
            # Inner Wall (-R)
            faces.extend([[ib2, ib1, it2], [ib1, it1, it2]])
            # Outer Wall (+R)
            faces.extend([[ob1, ob2, ot1], [ot1, ob2, ot2]])
            
        if abs((a2 - a1) - 2 * math.pi) > 1e-5:
            # Side Wall 1 (at i=0, normal -Theta)
            faces.extend([[0, 2, 1], [2, 3, 1]])
            
            # Side Wall 2 (at i=segs, normal +Theta)
            c = segs * 4
            faces.extend([[c, c+1, c+2], [c+1, c+3, c+2]])
        
        sector_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3): sector_mesh.vectors[i][j] = verts[f[j]]
        return sector_mesh

    # 3. Solid Floor with Drainage Holes (Spider Mount)
    # DELETED: We removed the bottom spider mount for Tiffany because it's printed upside down and bridging a 240mm gap is impossible.
    # The Tiffany shade will simply mount via the top finial hole on a standard harp.

    # 4. Flat Top Roof (Printed First / Upside Down)
    # The roof is completely solid except for a 4x2mm slit on the edge to break suction,
    # and a 10mm diameter center hole to mount to a standard lamp harp/finial.
    center_hole_r = 5.0 # 10mm diameter for ALL models
    
    # We create a solid inner ring. We stop 1mm before the inner wall so the slit can penetrate into the hollow cavity.
    inner_ring_outer = top_radius - 1.0 
    inner_ring_outer = max(center_hole_r + 2.0, inner_ring_outer)
    
    # Inner ring (solid 360 degrees, 2.0mm thick) - Adding 0.5mm overlap to weld with the outer ring perfectly
    meshes_to_concat.append(create_annular_sector(inner_ring_outer + 0.5, center_hole_r, height - 2.0, height - 2.0, 0, 2 * math.pi, 2.0, 60))
    
    # Outer ring (missing the slit section to form the 4x2mm opening at the back)
    segs1 = max(1, int(cols * (slit_start_angle / (2 * math.pi))))
    meshes_to_concat.append(create_annular_sector(top_radius + max_t + 0.5, inner_ring_outer, height - 2.0, height - 2.0, 0, slit_start_angle, 2.0, segs1, match_shape=True))
    
    segs2 = max(1, int(cols * ((2 * math.pi - slit_end_angle) / (2 * math.pi))))
    meshes_to_concat.append(create_annular_sector(top_radius + max_t + 0.5, inner_ring_outer, height - 2.0, height - 2.0, slit_end_angle, 2 * math.pi, 2.0, segs2, match_shape=True))

    final_mesh = mesh.Mesh(np.concatenate([m.data for m in meshes_to_concat]))
    final_mesh.save(os.path.join(job_path, "final.stl"))

if __name__ == "__main__":
    generate_unified_litho(
        sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]),
        float(sys.argv[6]) if len(sys.argv) > 6 else 120.0,
        float(sys.argv[7]) if len(sys.argv) > 7 else 100.0,
        float(sys.argv[8]) if len(sys.argv) > 8 else 3.0
    )
