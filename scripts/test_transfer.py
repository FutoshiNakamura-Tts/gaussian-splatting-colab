
import argparse
import os
import time
from utils import log, run_command

def test_tailscale_transfer(target_host):
    log(f"=== Testing Tailscale Transfer to {target_host} ===")
    
    # 1. Create a dummy file
    dummy_filename = "test_transfer.txt"
    with open(dummy_filename, "w") as f:
        f.write(f"This is a test file from Colab sent at {time.ctime()}")
    
    log(f"Created dummy file: {dummy_filename}")
    
    # 2. Add ':' to target if missing
    if not target_host.endswith(":"):
        target_host += ":"
        
    # 3. Transfer
    cmd = f"tailscale file cp {dummy_filename} {target_host}"
    log(f"Executing: {cmd}")
    
    success = run_command(cmd)
    
    if success:
        log("Transfer command returned success (0). Check your device's Drop inbox (Downloads folder).")
    else:
        log("Transfer failed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Tailscale File Transfer.")
    parser.add_argument("--target", type=str, required=True, help="Target Tailscale hostname (e.g., 'mypc')")
    args = parser.parse_args()
    
    test_tailscale_transfer(args.target)
