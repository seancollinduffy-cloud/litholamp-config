import subprocess
import os
import json
import re

# Dictionary mapping common friendly material names to their specific 8-character Formlabs codes.
FRIENDLY_TO_CODE = {
    "clear resin v4": "FLGPCL04",
    "clear v4": "FLGPCL04",
    "clear resin v5": "FLGPCL05",
    "clear v5": "FLGPCL05",
    "grey resin v4": "FLGPGY04",
    "grey v4": "FLGPGY04",
    "grey resin v5": "FLGPGY05",
    "grey v5": "FLGPGY05",
    "white resin v4": "FLGPWH04",
    "white v4": "FLGPWH04",
    "white resin v5": "FLGPWH05",
    "white v5": "FLGPWH05",
    "black resin v4": "FLGPBK04",
    "black v4": "FLGPBK04",
    "black resin v5": "FLGPBK05",
    "black v5": "FLGPBK05",
    "draft resin v2": "FLD5GR02",
    "draft v2": "FLD5GR02",
    "draft resin v3": "FLD5GR03",
    "draft v3": "FLD5GR03",
    "model resin v2": "FLMTG02",
    "model v2": "FLMTG02",
    "model resin v3": "FLMTG03",
    "model v3": "FLMTG03",
    "precision model": "FLMTG03",
    "tough 1500 v1": "FLTO1501",
    "tough 2000 v1": "FLTO2001",
    "durable v2": "FLDU02",
    "rigid 10k v1": "FLRG1001",
    "rigid 4k v1": "FLRG4K01",
    "high temp v2": "FLHT02",
    "flexible 80a v1": "FLFL8001",
    "elastic 50a v1": "FLEL5001",
    "castable wax v1": "FLCW0201",
    "castable wax 40 v1": "FLCW4001",
    "silicone 40a v1": "FLSI4001",
    "alumina 4n v1": "FLAL4N01",
    "ibt flex v1": "FLIBTF01",
    "surgical guide v1": "FLSG01",
    "dental lt clear v2": "FLDLTC02",
    "custom tray v1": "FLCT01",
}

def parse_material(material_str):
    """
    Parses a friendly material name or code into Formlabs name and version parameters.
    """
    clean_str = material_str.strip().lower()
    
    # Resolve friendly name to code
    code = FRIENDLY_TO_CODE.get(clean_str, material_str.strip())
    
    # Clean code: standard codes are alphanumeric (e.g. FLGPCL05, FLDU02, FLMTG03)
    # The last two characters are the version number.
    if len(code) >= 6 and code[-2:].isdigit():
        name = code[:-2].upper()
        version = int(code[-2:])
        return name, version
    
    # Fallback/default to Clear V5 if parsing is completely custom/unmatched
    print(f"Warning: Could not auto-detect material structure for '{material_str}'. Defaulting to Clear V5.")
    return "FLGPCL", 5

def run_headless_preform(stl_path, material_config, output_form_path, scale=1.0):
    """
    Runs Preform in headless mode to process an STL, auto-orient, 
    auto-support, and generate print time/volume metrics.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check for HeadlessPreForm.exe or preform.exe in the Headless_PreForm folder
    preform_executable = os.path.join(script_dir, "Headless_PreForm", "HeadlessPreForm.exe")
    if not os.path.exists(preform_executable):
        preform_executable = os.path.join(script_dir, "Headless_PreForm", "preform.exe")

    if not os.path.exists(preform_executable):
        print(f"Error: Could not find Preform executable at: {preform_executable}")
        return None

    # Step 1: Parse material configuration and select printer type
    material_name, material_version = parse_material(material_config)
    
    # Decide machine type based on material version (V4 is Form 3, V5 and others are Form 4)
    machine_type = "Form 3" if material_version == 4 else "Form 4"
    
    # Use absolute paths for the job configuration files
    abs_stl_path = os.path.abspath(stl_path)
    abs_output_form_path = os.path.abspath(output_form_path)
    
    # Paths for temporary job files
    prepare_job_path = os.path.join(script_dir, "temp_prepare_job.json")
    estimate_job_path = os.path.join(script_dir, "temp_estimate_job.json")

    # Create the scene preparation JSON descriptor
    prepare_job = {
        "action": "prepare",
        "version": 1,
        "input": {
            "kind": "SCENE_SETTINGS",
            "version": 1,
            "global": {
                "kind": "GLOBAL_SETTINGS",
                "version": 1,
                "machine_type": machine_type,
                "material": {
                    "type": {
                        "name": material_name,
                        "version": material_version
                    },
                    "thickness_mm": 0.1
                },
                "layout": "auto",
                "repair_behavior": "repair"
            },
            "models": [
                {
                    "model_file": abs_stl_path,
                    "settings": {
                        "kind": "MODEL_SETTINGS",
                        "version": 1,
                        "scale": scale,
                        "units": "mm",
                        "orientation": "auto",
                        "support_settings": {
                            "raft_type": "FULL_RAFT",
                            "density": 1.0,
                            "touchpoint_size_mm": 0.3,
                            "internal_supports_enabled": False
                        }
                    }
                }
            ]
        },
        "output": abs_output_form_path
    }

    # Create the scene estimation JSON descriptor
    estimate_job = {
        "action": "estimate",
        "version": 1,
        "input": abs_output_form_path
    }

    metrics = {
        "print_time_s": 0,
        "volume_mL": 0.0,
        "layer_count": 0
    }

    try:
        # Write prepare job
        with open(prepare_job_path, 'w') as f:
            json.dump(prepare_job, f, indent=4)
            
        print(f"Running Preform preparation for '{stl_path}'...")
        args_prepare = [preform_executable, "run", prepare_job_path, "--progress-as-json"]
        result_prepare = subprocess.run(args_prepare, capture_output=True, text=True, check=True)
        
        # Parse output for layer count and volume
        for line in result_prepare.stdout.splitlines():
            if line.startswith("{"):
                try:
                    data = json.loads(line)
                    if data.get("type") == "PrintDetailsMessage":
                        msg = data.get("message", {})
                        meta = msg.get("metadata", {})
                        if "Scene" in meta:
                            metrics["layer_count"] = meta["Scene"].get("Height_Layers", metrics["layer_count"])
                        elif "Model" in meta:
                            # Model volume in cubic mm converted to mL (1 mL = 1000 cubic mm)
                            vol_mm3 = meta["Model"].get("ResinVolume_mm3", 0)
                            metrics["volume_mL"] = round(vol_mm3 / 1000.0, 2)
                except json.JSONDecodeError:
                    pass

        # Write estimate job
        with open(estimate_job_path, 'w') as f:
            json.dump(estimate_job, f, indent=4)
            
        print(f"Calculating print metrics on generated FORM file...")
        args_estimate = [preform_executable, "run", estimate_job_path, "--progress-as-json"]
        result_estimate = subprocess.run(args_estimate, capture_output=True, text=True, check=True)

        print("\nRAW ESTIMATE STDOUT:")
        print(result_estimate.stdout)
        print("--------------------")

        # Parse output for final print duration and volume
        for line in result_estimate.stdout.splitlines():
            if line.startswith("{"):
                try:
                    data = json.loads(line)
                    if data.get("type") == "TaskStatus":
                        msg = data.get("message", {})
                        if msg.get("status") == "SUCCEEDED" and "result" in msg:
                            res = msg.get("result", {})
                            dur_min = res.get("duration_min", 0.0)
                            metrics["print_time_s"] = int(dur_min * 60)
                            metrics["volume_mL"] = round(res.get("volume_mL", metrics["volume_mL"]), 2)
                except json.JSONDecodeError:
                    pass
        
        print("Preform processing complete.")
        return metrics

    except subprocess.CalledProcessError as e:
        print(f"Error running Preform: {e.stderr}")
        return None
    finally:
        pass

if __name__ == "__main__":
    test_stl_file = "test_part.stl" 
    target_material = "Clear Resin V4" # Example material (FLGPCL04 -> V4 -> Form 3)
    output_file = "ready_to_print.form"
    
    if os.path.exists(test_stl_file):
        print(f"Found {test_stl_file}, starting test...")
        metrics = run_headless_preform(test_stl_file, target_material, output_file)
        
        print("\n--- Preform Output Metrics ---")
        print(json.dumps(metrics, indent=4))
        print("------------------------------")
        
        # Test 2: Try with V5 resin (FLGPCL05 -> V5 -> Form 4)
        target_material_v5 = "Clear Resin V5"
        output_file_v5 = "ready_to_print_v5.form"
        print(f"Starting test with {target_material_v5}...")
        metrics_v5 = run_headless_preform(test_stl_file, target_material_v5, output_file_v5)
        print("\n--- Preform V5 Output Metrics ---")
        print(json.dumps(metrics_v5, indent=4))
        print("---------------------------------")
    else:
        print(f"Test bypassed: Please place a 3D model named '{test_stl_file}' in this directory to run the test.")
