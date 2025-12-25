
import os
import shutil
import argparse
import glob
from utils import log, run_command

def zip_output(output_path):
    log(f"Zipping output directory: {output_path}...")
    base_name = os.path.basename(output_path.rstrip('/'))
    zip_path = f"{output_path}.zip"
    
    # shutil.make_archive creates the zip file. 
    # root_dir is the parent, base_dir is the directory itself.
    root_dir = os.path.dirname(output_path)
    base_dir = base_name
    
    shutil.make_archive(output_path, 'zip', root_dir, base_dir)
    log(f"Created zip: {zip_path}")
    return zip_path

def transfer_results(output_path, drive_dest=None, tailscale_target=None):
    if not os.path.exists(output_path):
        log(f"Error: Output path {output_path} does not exist. Cannot transfer.")
        return

    # 1. Zip the output
    zip_path = zip_output(output_path)
    
    # 2. Transfer to Google Drive
    if drive_dest:
        log(f"Copying to Google Drive: {drive_dest}...")
        try:
            if not os.path.exists(drive_dest) and drive_dest.startswith("/content/drive"):
                 # Try to create directory if it's a folder path and doesn't exist
                 # But usually drive_dest assumes a mounted path.
                 # If it looks like a file path, valid. If directory, we copy into it.
                 pass
            
            shutil.copy(zip_path, drive_dest)
            log("Copy to Drive successful.")
        except Exception as e:
            log(f"Error copying to Drive: {e}")

    # 3. Transfer via Tailscale
    if tailscale_target:
        target = tailscale_target
        if not target.endswith(":"):
            target += ":"
        
        log(f"Sending via Tailscale to {target}...")
        cmd = f"tailscale file cp {zip_path} {target}"
        if run_command(cmd):
            log("Tailscale transfer initiated.")
        else:
            log("Tailscale transfer failed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Post-training processing.")
    parser.add_argument("--output_path", type=str, required=True, help="Path to the output directory")
    parser.add_argument("--drive_dest", type=str, default=None, help="Destination path on Google Drive (optional)")
    parser.add_argument("--tailscale_target", type=str, default=None, help="Tailscale target hostname (optional)")
    
    args = parser.parse_args()
    
    transfer_results(args.output_path, args.drive_dest, args.tailscale_target)
