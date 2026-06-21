import os
import shutil
from PIL import Image
from cylinder_render import generate_unified_litho

def generate_blank_stls():
    os.makedirs("blank_stls", exist_ok=True)
    
    # Create a blank white image
    img = Image.new('L', (600, 600), color=255)
    img.save("blank_stls/input_0.png")
    
    configs = [
        {"name": "RoundWoodBase", "hardware": "RoundWoodBase", "shape": "Cylinder", "sides": 1, "h": 120, "d": 90},
        {"name": "SquareWoodBase", "hardware": "SquareWoodBase", "shape": "Square", "sides": 4, "h": 120, "d": 90},
        {"name": "DarkWoodBase", "hardware": "DarkWoodBase", "shape": "Cylinder", "sides": 1, "h": 120, "d": 90},
        {"name": "TiffanyDesk", "hardware": "TiffanyDesk", "shape": "Tiffany", "sides": 1, "h": 140, "d": 160},
        {"name": "TiffanyFloor", "hardware": "TiffanyFloor", "shape": "Tiffany", "sides": 1, "h": 180, "d": 200},
    ]
    
    for c in configs:
        print(f"Generating blank STL for {c['name']}...")
        out_dir = os.path.join("blank_stls", c['name'])
        os.makedirs(out_dir, exist_ok=True)
        shutil.copy("blank_stls/input_0.png", os.path.join(out_dir, "input_0.png"))
        
        generate_unified_litho(
            out_dir, 
            c['hardware'], 
            c['shape'], 
            c['sides'], 
            1, 
            c['h'], 
            c['d'], 
            4.0
        )
        shutil.copy(os.path.join(out_dir, "final.stl"), f"blank_stls/{c['name']}.stl")
        
    print("Done!")

if __name__ == "__main__":
    generate_blank_stls()
