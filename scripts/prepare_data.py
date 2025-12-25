
import os
import sys
import argparse
import shutil
import glob
from utils import log, run_command

def prepare_data(source_type, path_or_url=None):
    log(f"=== Preparing Data: {source_type} ===")
    
    # Target directory for data
    # Note: Gaussian Splatting expects source to be passed to train.py, 
    # but we usually assume some standard location or just use the path provided.
    
    if source_type == "Demo Data":
        # Keep existing Demo Data logic (Truck)
        if not os.path.exists("/content/tandt"):
             log("Downloading TandT Truck dataset...")
             run_command("wget https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/input/tandt_db.zip")
             run_command("unzip -q tandt_db.zip -d /content/tandt")
        else:
             log("Demo data already present.")
             
    elif source_type == "User Data (Path)":
        if not path_or_url:
            log("Error: No path provided for User Data.")
            return

        if not os.path.exists(path_or_url):
            log(f"Error: Path '{path_or_url}' does not exist on this system.")
            log("Please use 'scripts/local_transfer.sh upload' to transfer your data first.")
            return
            
        log(f"Validating data at: {path_or_url}")
        
        # Basic check for COLMAP output or images
        has_images = os.path.exists(os.path.join(path_or_url, "images"))
        has_sparse = os.path.exists(os.path.join(path_or_url, "sparse"))
        
        if has_images and has_sparse:
            log("Structure looks correct (images + sparse). Ready for training.")
        elif has_images and not has_sparse:
            log("WARNING: Found 'images' but no 'sparse' folder.")
            log("    If this is raw image data, you may need to run COLMAP (convert.py) manually.")
            log("    (Automatic COLMAP execution is not yet implemented in this simplified script)")
        else:
            log("WARNING: Directory structure unclear. Ensure it contains 'images' and COLMAP 'sparse' output if pre-processed.")

    else:
        log(f"Unknown source type: {source_type}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare Data Script")
    parser.add_argument("--source", type=str, required=True, help="Source Type")
    parser.add_argument("--path", type=str, default=None, help="Path or URL")
    
    args = parser.parse_args()
    prepare_data(args.source, args.path)
