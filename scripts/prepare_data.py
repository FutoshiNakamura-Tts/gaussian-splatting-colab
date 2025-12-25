
import os
import sys
import shutil
import argparse
from utils import log, run_command

def prepare_data(source_type, path_or_url=None, save_zip=False):
    log(f"=== Preparing Data: {source_type} ===")
    os.chdir('/content')
    
    if source_type == "Demo Data":
        if not os.path.exists('tandt_db'):
            log("Downloading TandT Demo Data...")
            run_command("wget -q https://huggingface.co/camenduru/gaussian-splatting/resolve/main/tandt_db.zip")
            run_command("unzip -q tandt_db.zip")
        else:
            log("Demo data already exists.")

    elif source_type == "Google Drive":
        if not path_or_url:
            log("Error: No Drive path provided.")
            return

        drive_path_val = path_or_url
        if not os.path.exists(drive_path_val):
            log(f"Error: Drive Path {drive_path_val} does not exist. Mount drive first?")
            return
        
        if os.path.isfile(drive_path_val):
             fname = os.path.basename(drive_path_val)
             if fname.lower().endswith('.zip'):
                 log(f"Copying and unzipping {fname}...")
                 shutil.copy(drive_path_val, f"./{fname}")
                 run_command(f"unzip -q \"{fname}\"")
             else:
                 log(f"Copying {fname}...")
                 shutil.copy(drive_path_val, ".")
        elif os.path.isdir(drive_path_val):
            log(f"Target is a directory: {drive_path_val}. Using it directly.")

    elif source_type == "Custom URL":
        custom_url_val = path_or_url
        if not custom_url_val:
             log("Error: Custom URL is empty.")
             return
        log(f"Downloading from {custom_url_val}...")
        fname = os.path.basename(custom_url_val)
        if '?' in fname: fname = fname.split('?')[0]
        if not fname: fname = "downloaded_data.zip"

        run_command(f"wget -q -O {fname} {custom_url_val}")
        
        if fname.lower().endswith('.zip'):
            log(f"Unzipping {fname}...")
            run_command(f"unzip -q \"{fname}\"")
        else:
            log(f"Downloaded {fname}.")
            
    elif source_type == "Local Folder": # Assumed to be on the server already
        local_folder_val = path_or_url
        if not local_folder_val or not os.path.exists(local_folder_val):
             log(f"Error: Path {local_folder_val} does not exist.")
             return
        log(f"Using Local Folder: {local_folder_val}")

    # Note: 'Upload Zip' logic is handled by the Frontend (notebook) putting the file there, 
    # or by user scp-ing the file. This script assumes the file might already be there or passed via path.
    # For now, we support "File Path" as a generic handler if the zip is uploaded to /content.
    elif source_type == "File Path":
         fpath = path_or_url
         if not os.path.exists(fpath):
             log(f"Error: File {fpath} not found.")
             return
         
         if fpath.lower().endswith('.zip'):
             log(f"Unzipping {fpath}...")
             run_command(f"unzip -q \"{fpath}\"")
         else:
             log(f"Using file {fpath}")

    log("Data preparation complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Prepare data for Gaussian Splatting.")
    parser.add_argument("--source", type=str, default="Demo Data", 
                        choices=["Demo Data", "Google Drive", "Custom URL", "Local Folder", "File Path"], 
                        help="Type of data source")
    parser.add_argument("--path", type=str, default="", help="Path or URL for the data")
    
    args = parser.parse_args()
    
    prepare_data(args.source, args.path)
