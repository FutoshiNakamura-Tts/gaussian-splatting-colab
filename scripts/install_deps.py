
import os
import sys
import argparse
import glob
from utils import log, run_command

def install_dependencies(accelerated=False):
    log("=== Installing Dependencies ===")
    os.chdir('/content')
    
    # Rasterizer Selection
    rasterizer_branch = 'main'
    is_accelerated = False
    if accelerated:
        rasterizer_branch = '3dgs_accel'
        is_accelerated = True
        log("Selected Accelerated Rasterizer (Sparse Adam).")
    else:
        log("Selected Standard Rasterizer.")

    # Clone Wheels Repo
    if not os.path.exists('/content/wheels_repo'):
         log("Cloning wheels repo...")
         run_command("git clone -b colab-t4-2025-12-18 https://github.com/FutoshiNakamura-Tts/gaussian-splatting-colab /content/wheels_repo")
    
    # Clone Gaussian Splatting Repo
    repo_dir = '/content/gaussian-splatting'
    if not os.path.exists(repo_dir):
         log(f"Cloning gaussian-splatting...")
         run_command(f"git clone --recursive https://github.com/graphdeco-inria/gaussian-splatting {repo_dir}")
    
    log("Installing plyfile...")
    run_command(f"{sys.executable} -m pip install -q plyfile")

    # Handle Submodules (Diff-Gaussian-Rasterization)
    dgr_dir = f"{repo_dir}/submodules/diff-gaussian-rasterization"
    sknn_dir = f"{repo_dir}/submodules/simple-knn"
    
    try:
        log(f"Configuring diff-gaussian-rasterization to branch: {rasterizer_branch}")
        # Unconditionally fetch and checkout desired branch for submodule
        run_command(f"git -C {dgr_dir} fetch origin {rasterizer_branch}")
        run_command(f"git -C {dgr_dir} checkout {rasterizer_branch}")
    except Exception as e:
        log(f"Error configuring submodule: {e}")

    log("Checking for bundled wheels or building submodules...")
    
    packages = [
        {"name": "diff-gaussian-rasterization", "pattern": "diff_gaussian_rasterization-*-cp*-*-linux_x86_64.whl", "src": dgr_dir},
        {"name": "simple-knn", "pattern": "simple_knn-*-cp*-*-linux_x86_64.whl", "src": sknn_dir}
    ]
    
    for pkg in packages:
        wheel_to_install = None
        
        # 1. If Accelerated, check subfolder first
        if is_accelerated:
            accel_wheels = glob.glob(f"/content/wheels_repo/wheels/3dgs_accel/{pkg['pattern']}")
            if accel_wheels:
                wheel_to_install = accel_wheels[0]
                log(f"Found Accelerated wheel for {pkg['name']}: {wheel_to_install}")
        
        # 2. Check root wheels folder (Fallback or Standard)
        if not wheel_to_install:
             # Only allow fallback if NOT (Accelerated Mode AND diff-gaussian-rasterization)
             # simple-knn is safe to fallback as it is shared
             allow_fallback = not (is_accelerated and pkg['name'] == 'diff-gaussian-rasterization')
             
             if allow_fallback:
                 standard_wheels = glob.glob(f"/content/wheels_repo/wheels/{pkg['pattern']}")
                 if standard_wheels:
                     wheel_to_install = standard_wheels[0]
                     log(f"Found Standard/Shared wheel for {pkg['name']}: {wheel_to_install}")
             elif is_accelerated:
                 log(f"Skipping standard wheel fallback for {pkg['name']} to force source build from 3dgs_accel branch.")

        if wheel_to_install:
            run_command(f"{sys.executable} -m pip install --force-reinstall -q {wheel_to_install}")
        else:
            log(f"No wheel found for {pkg['name']}. Building from source...")
            run_command(f"{sys.executable} -m pip install --force-reinstall -q {pkg['src']}")

    log("Dependencies installed.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Install dependencies for Gaussian Splatting.")
    parser.add_argument("--accelerated", action="store_true", help="Use Accelerated Rasterizer (Sparse Adam)")
    args = parser.parse_args()
    
    install_dependencies(args.accelerated)
