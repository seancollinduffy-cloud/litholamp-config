import os
import math
import numpy as np
from stl import mesh

def create_cylinder(radius, height, z_offset=0, segs=32, angle_offset=0, top_radius=None):
    if top_radius is None: top_radius = radius
    verts = []
    faces = []
    
    verts.append([0, 0, z_offset])
    verts.append([0, 0, z_offset + height])
    
    for i in range(segs):
        a = (i / segs) * 2 * math.pi + angle_offset
        verts.append([radius * math.cos(a), radius * math.sin(a), z_offset])
        verts.append([top_radius * math.cos(a), top_radius * math.sin(a), z_offset + height])
        
    for i in range(segs):
        cn = (i + 1) % segs
        b1, t1 = 2 + i*2, 2 + i*2 + 1
        b2, t2 = 2 + cn*2, 2 + cn*2 + 1
        
        faces.append([0, b2, b1])
        faces.append([1, t1, t2])
        faces.append([b1, b2, t1])
        faces.append([b2, t2, t1])
        
    out_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, f in enumerate(faces):
        for j in range(3): out_mesh.vectors[i][j] = verts[f[j]]
    return out_mesh

def combine(meshes):
    return mesh.Mesh(np.concatenate([m.data for m in meshes]))

# 1. Round Wood Base
round_body = create_cylinder(45, 20, -20, 64)
round_led = create_cylinder(35, 2, -2, 64)
round_mesh = combine([round_body, round_led])

# 2. Square Wood Base
# Width 90x90 means diagonal radius is 90 * sqrt(2) / 2 = 63.64
square_body = create_cylinder(63.64, 20, -20, 4, math.pi / 4)
square_led = create_cylinder(35, 2, -2, 64)
square_mesh = combine([square_body, square_led])

# 3. Dark Wood Base (Geometrically same as Round Wood Base)
dark_mesh = combine([round_body, round_led])

# 4. Tiffany Desk Lamp
# Intricate antique bronze cone base and stem
desk_base = create_cylinder(60, 15, -15, 64, top_radius=40)
desk_stem = create_cylinder(10, 100, -115, 32)
desk_bottom = create_cylinder(70, 10, -125, 64, top_radius=60)
tiffany_desk_mesh = combine([desk_base, desk_stem, desk_bottom])

# 5. Tiffany Floor Lamp
# Heavy wide floor base with a tall stem
floor_base = create_cylinder(80, 20, -20, 64, top_radius=50)
floor_stem = create_cylinder(12, 400, -420, 32)
floor_bottom = create_cylinder(120, 30, -450, 64, top_radius=80)
tiffany_floor_mesh = combine([floor_base, floor_stem, floor_bottom])

os.makedirs("../litholamp-web/public/models", exist_ok=True)
os.makedirs("../voronoid-web/public/models", exist_ok=True)

models = [
    ("RoundWoodBase", round_mesh),
    ("SquareWoodBase", square_mesh),
    ("DarkWoodBase", dark_mesh),
    ("TiffanyDesk", tiffany_desk_mesh),
    ("TiffanyFloor", tiffany_floor_mesh)
]

for name, m in models:
    m.save(f"../litholamp-web/public/models/{name}.stl")
    m.save(f"../voronoid-web/public/models/{name}.stl")
    print(f"Saved {name}.stl")
