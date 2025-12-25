
import os
import sys
import subprocess
import time

def log(msg):
    """Logs a message to stdout with timestamp."""
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {msg}", flush=True)

def run_command(cmd, shell=True, env=None, cwd=None):
    """Runs a shell command and logs its output."""
    try:
        log(f"Executing: {cmd}")
        process = subprocess.Popen(
            cmd, shell=shell, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True,
            env=env,
            cwd=cwd
        )
        for line in process.stdout:
            print(line, end='', flush=True) # Already contains newline from subprocess
        
        process.wait()
        if process.returncode != 0:
             log(f"Command failed with return code {process.returncode}")
             return False
        return True
    except Exception as e:
        log(f"Error executing command: {e}")
        return False
