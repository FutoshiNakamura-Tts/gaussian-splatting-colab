
import os
import sys
from utils import log, run_command

def check_gpu():
    log("Checking GPU...")
    if run_command("nvidia-smi"):
        log("GPU is available.")
    else:
        log("WARNING: GPU might not be available or nvidia-smi failed.")

def check_drive_mount():
    drive_path = '/content/drive'
    if os.path.exists(drive_path):
        log(f"Google Drive is mounted at {drive_path}.")
    else:
        log("Google Drive is NOT mounted. (If running in Colab, please mount via the GUI wrapper or runtime menu if needed for backup).")

if __name__ == "__main__":
    log("=== Setting up Environment ===")
    check_gpu()
    check_drive_mount()
    log("Environment setup complete.")
