
import os
import sys
import argparse
import shlex
import torch
from utils import log, run_command
import post_train

def train(args):
    log("=== Starting Training ===")
    os.chdir('/content/gaussian-splatting')
    
    cmd_parts = [sys.executable, "train.py"]
    cmd_parts.extend(["-s", args.source_path])
    cmd_parts.extend(["-m", args.output_path])
    cmd_parts.extend(["--iterations", str(args.iterations)])
    cmd_parts.extend(["--sh_degree", str(args.sh_degree)])
    
    if args.white_background: cmd_parts.append("-w")
    if args.eval: cmd_parts.append("--eval")
    
    # New Features
    if args.antialiasing: cmd_parts.append("--antialiasing")
    
    if args.exposure:
        cmd_parts.extend(["--exposure_lr_init", "0.001", "--exposure_lr_final", "0.0001", "--exposure_lr_delay_steps", "5000", "--exposure_lr_delay_mult", "0.001", "--train_test_exp"])
        
    if args.depth and args.depth_path:
        cmd_parts.extend(["-d", args.depth_path])
    
    if args.sparse_adam:
        cmd_parts.extend(["--optimizer_type", "sparse_adam"])

    cmd = " ".join(shlex.quote(arg) for arg in cmd_parts)
    
    if args.dry_run or not torch.cuda.is_available():
        log("--- Dry Run Mode or No GPU ---")
        log(f"Command: {cmd}")
        # In dry run, we don't actually run training, so output dir might not exist.
        pass
    else:
        log(f"Executing: {cmd}")
        if run_command(cmd):
            log("Training finished successfully.")
            
            # Post Training Hook
            log("--- Running Post-Training Tasks ---")
            post_train.transfer_results(
                args.output_path, 
                args.drive_dest, 
                args.tailscale_target
            )
        else:
            log("Training failed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Gaussian Splatting Training.")
    
    # Standard Params
    parser.add_argument("--source_path", type=str, required=True, help="Path to source images/colmap")
    parser.add_argument("--output_path", type=str, required=True, help="Path to output directory")
    parser.add_argument("--iterations", type=int, default=30000)
    parser.add_argument("--sh_degree", type=int, default=3)
    parser.add_argument("--white_background", action="store_true")
    parser.add_argument("--eval", action="store_true")
    
    # New Features
    parser.add_argument("--antialiasing", action="store_true")
    parser.add_argument("--exposure", action="store_true")
    parser.add_argument("--depth", action="store_true")
    parser.add_argument("--depth_path", type=str, default="")
    parser.add_argument("--sparse_adam", action="store_true")
    
    # Execution Control
    parser.add_argument("--dry_run", action="store_true")
    
    # Transfer Params
    parser.add_argument("--drive_dest", type=str, default=None, help="Copy result zip to this Drive path")
    parser.add_argument("--tailscale_target", type=str, default=None, help="Send result zip to this Tailscale host")

    args = parser.parse_args()
    train(args)
