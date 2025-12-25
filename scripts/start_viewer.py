
import os
import sys
import argparse
import glob
import subprocess
import socket
import time
from utils import log, run_command

def start_viewer(output_path, ply_file=None, port=8000, embedded=False):
    log("=== Starting Viewer ===")
    
    # 1. Setup Viewer Directory
    viewer_dir = '/content/viewer'
    if not os.path.exists(viewer_dir):
        log("Cloning antimatter15/splat viewer...")
        run_command(f"git clone https://github.com/antimatter15/splat {viewer_dir}")
    
    # 2. Determine Point Cloud File
    target_ply = None
    
    if ply_file and os.path.exists(ply_file):
        target_ply = ply_file
        log(f"Using selected file: {target_ply}")
    elif output_path and os.path.exists(output_path):
         # Prefer latest iteration
        ply_files = glob.glob(f"{output_path}/point_cloud/iteration_*/point_cloud.ply")
        if ply_files:
            try:
                ply_files.sort(key=lambda x: int(x.split('iteration_')[1].split('/')[0]))
            except:
                pass 
            target_ply = ply_files[-1]
            log(f"Auto-detected file: {target_ply}")
    
    # 3. Symlink/Copy to viewer dir
    link_dst = f"{viewer_dir}/input.ply"
    if os.path.exists(link_dst):
        os.remove(link_dst)
        
    url_param = ""
    if target_ply:
        os.symlink(target_ply, link_dst)
        url_param = "input.ply"
    else:
        log("No input file found. Viewer will start in empty/default mode.")
    
    # 4. Create Custom Server Script (for COOP/COEP headers)
    server_script_path = f"{viewer_dir}/simple_server.py"
    with open(server_script_path, 'w') as f:
        f.write('''
from http.server import HTTPServer, SimpleHTTPRequestHandler
import sys

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    print(f"Serving on port {port} with COOP/COEP headers...")
    httpd.serve_forever()
''')

    # 5. Start HTTP Server
    log(f"Starting HTTP Server on port {port} in {viewer_dir}...")
    run_command(f"fuser -k {port}/tcp || true") 
    
    subprocess.Popen([sys.executable, "simple_server.py", str(port)], cwd=viewer_dir)
    
    log("Waiting for server to start...")
    max_retries = 10
    server_ready = False
    for i in range(max_retries):
         try:
             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                 if s.connect_ex(('localhost', port)) == 0:
                     server_ready = True
                     break
         except:
             pass
         time.sleep(0.5)
         
    if server_ready:
        log(f"Server is ready on port {port}.")
        if embedded:
            log("NOTE: To embed in Colab, use the Notebook GUI which handles proxy URL detection.")
    else:
        log("[WARNING] Server might not be ready.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start 3DGS Viewer.")
    parser.add_argument("--output_path", type=str, default=None, help="Path to training output (to auto-find ply)")
    parser.add_argument("--ply_file", type=str, default=None, help="Specific ply file path")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--embedded", action="store_true", help="Flag to indicate embedded intent (logging only)")
    
    args = parser.parse_args()
    
    start_viewer(args.output_path, args.ply_file, args.port, args.embedded)
