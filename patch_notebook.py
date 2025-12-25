import json
import os
import glob # Need this if we run the code, but for string it's fine.

nb_path = '/home/nakamura/git/gaussian-splatting-colab/gaussian_splatting_colab.ipynb'

# Use triple double quotes for the outer string to avoid conflict with inner triple single quotes
new_start_viewer_source = r"""# @title 3.1 Define Actions (Viewer)
# ===========================
# Viewer Actions
# ===========================

def start_viewer(b):
    out.clear_output()
    log("=== 5. Starting Viewer ===")
    
    # 1. Setup Viewer Directory
    viewer_dir = '/content/viewer'
    if not os.path.exists(viewer_dir):
        log("Cloning antimatter15/splat viewer...")
        run_command(f"git clone https://github.com/antimatter15/splat {viewer_dir}")
    
    # 2. Determine Point Cloud File
    ply_file = None
    
    # Check Widget Input
    if 'txt_viewer_path' in globals() and txt_viewer_path.value:
        custom_ply = txt_viewer_path.value
        if os.path.exists(custom_ply):
            ply_file = custom_ply
            log(f"Using selected file: {ply_file}")
        else:
            log(f"[WARNING] Selected file not found: {custom_ply}")
    
    # Auto-detect if no custom file
    if not ply_file and os.path.exists(Output_Path):
        # Prefer latest iteration
        ply_files = glob.glob(f"{Output_Path}/point_cloud/iteration_*/point_cloud.ply")
        if ply_files:
            try:
                ply_files.sort(key=lambda x: int(x.split('iteration_')[1].split('/')[0]))
            except:
                pass 
            ply_file = ply_files[-1]
            log(f"Auto-detected file: {ply_file}")
    
    # 3. Symlink/Copy to viewer dir
    target_ply = f"{viewer_dir}/input.ply"
    if os.path.exists(target_ply):
        os.remove(target_ply)
        
    if ply_file:
        # Create symlink for the viewer to load by default
        # Viewer loads 'input.ply' if no url param, or we can force it.
        # Symlinking is safe.
        os.symlink(ply_file, target_ply)
        url_param = "input.ply"
    else:
         log("No input file found. Viewer will start in empty/default mode.")
         log("You can Drag & Drop a .ply file into the viewer window.")
         url_param = ""

    
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
    port = 8000
    log(f"Starting HTTP Server on port {port} in {viewer_dir}...")
    run_command(f"fuser -k {port}/tcp || true") 
    
    # Use the custom script instead of http.server module
    subprocess.Popen([sys.executable, "simple_server.py", str(port)], cwd=viewer_dir)
    
    # WAIT for server to be ready
    log("Waiting for server to start...")
    max_retries = 10
    server_ready = False
    import socket
    import time
    for i in range(max_retries):
         try:
             # Just check if port is listening (simple check)
             with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                 if s.connect_ex(('localhost', port)) == 0:
                     server_ready = True
                     break
         except:
             pass
         time.sleep(0.5)
         
    if not server_ready:
        log("[WARNING] Server might not be ready, but proceeding...")
    else:
        log("Server is ready.")
    
    # 6. Access Links
    from google.colab import output
    from google.colab.output import eval_js
    from IPython.display import IFrame, display
    
    viewer_path = "/index.html"
    if url_param:
        viewer_path += f"?url={url_param}"
        
    # Proxy Link
    proxy_url = None
    try:
        import signal
        def handler(signum, frame):
            raise TimeoutError("Proxy resolution timed out")
        
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(5) # 5 second timeout
        
        try:
            proxy_base = eval_js(f"google.colab.kernel.proxyPort({port})")
        except TimeoutError:
            log("Proxy resolution timed out. Proceeding without Proxy URL.")
            proxy_base = None
        finally:
            signal.alarm(0)

        if proxy_base:
            proxy_url = f"{proxy_base}{viewer_path}"
            log(f"\\n\ud83c\udf0d Public Proxy URL: {proxy_url}")
    except Exception as e:
        log(f"Could not detect proxy url: {e}")
        
    # Tailscale Link
    if 'tailscale_conn' in globals() and tailscale_conn.connected:
        log(f"\ud83d\udd17 Tailscale URL: http://colab:{port}{viewer_path}")

    # 7. Embed (Optional)
    if 'cb_embedded' in globals() and cb_embedded.value:
        log("Embedding viewer...")
        out_viewer.clear_output()
        if proxy_url:
             with out_viewer:
                 # Use IFrame directly with the proxy URL for better control/reliability
                 display(IFrame(src=proxy_url, width='100%', height='600'))
        else:
             log("[ERROR] Cannot embed viewer: Proxy URL not found.")
    else:
        log("Viewer started (Embedding disabled).")
"""

new_gui_controller_source = r"""# @title 4.2. GUI Controller (Logic)
# ===========================
# Event binding and Logic
# ===========================
import os


class GUIController:
    def __init__(self, view):
        self.view = view
        self.current_path = os.getcwd()
        self.current_path_v = os.getcwd() # Separate path state for viewer browser
        self.active_input = None
        
        # Init browsers
        self._update_browser(self.view.sel_files, self.view.lbl_path, self.current_path)
        self._update_browser(self.view.sel_files_v, self.view.lbl_path_v, self.current_path_v)

        # Bind events last to ensure all methods are defined
        self._bind_events()

    def _bind_events(self):
        # Tailscale
        if 'tailscale_conn' in globals():
            self.view.cb_tailscale.observe(self._on_tailscale_change, names='value')
            tailscale_conn.status_callback = lambda msg: setattr(self.view.lbl_tailscale_status, 'value', msg)
        
        # Visibility Logic
        self.view.dd_rasterizer.observe(self._on_rasterizer_change, names='value')
        self.view.cb_depth.observe(self._on_depth_change, names='value')
        self.view.dd_datasource.observe(self._on_datasource_change, names='value')
        
        # File Browser 1 (Source)
        self.view.btn_browse.on_click(lambda b: self._open_browser_source(self.view.txt_source_path, "Source Path"))
        self.view.btn_up.on_click(lambda b: self._on_up(self.view.sel_files, self.view.lbl_path, is_viewer=False))
        self.view.sel_files.observe(lambda change: self._on_select_item(change, self.view.sel_files, self.view.lbl_path, is_viewer=False), names='value')
        self.view.btn_select.on_click(lambda b: self._on_confirm_select(self.view.browser_box, self.view.sel_files, is_viewer=False))
        self.view.btn_cancel_browser.on_click(lambda b: self._on_cancel_browser(self.view.browser_box))

        # File Browser 2 (Viewer)
        self.view.btn_browse_viewer.on_click(lambda b: self._open_browser_viewer(self.view.txt_viewer_path, "Viewer File"))
        self.view.btn_up_v.on_click(lambda b: self._on_up(self.view.sel_files_v, self.view.lbl_path_v, is_viewer=True))
        self.view.sel_files_v.observe(lambda change: self._on_select_item(change, self.view.sel_files_v, self.view.lbl_path_v, is_viewer=True), names='value')
        self.view.btn_select_v.on_click(lambda b: self._on_confirm_select(self.view.browser_box_viewer, self.view.sel_files_v, is_viewer=True))
        self.view.btn_cancel_browser_v.on_click(lambda b: self._on_cancel_browser(self.view.browser_box_viewer))
        
        # Actions with Async Feedback
        self.view.btn_env.on_click(lambda b: self._run_action("Setting up Env...", setup_env))
        self.view.btn_deps.on_click(lambda b: self._run_action("Installing Deps...", install_deps))
        self.view.btn_data.on_click(lambda b: self._run_action("Preparing Data...", prepare_data))
        self.view.btn_train.on_click(lambda b: self._run_action("Training...", start_training))
        self.view.btn_view.on_click(lambda b: self._run_action("Starting Viewer...", start_viewer))
        self.view.btn_stop_viewer.on_click(self._on_stop_viewer)

    def _run_action(self, msg, func):
        self.view.set_status('busy', msg)
        for w in self.view.lockable_widgets:
            w.disabled = True

        try:
            func(None)
        except Exception as e:
            log(f"Error: {e}")
        finally:
            self.view.set_status('ready', "")
            for w in self.view.lockable_widgets:
                w.disabled = False
    
    def _on_stop_viewer(self, b):
        self.view.set_status('busy', "Stopping Viewer...")
        try:
             # Kill port 8000
             # We use fuser to kill the process on port 8000
             run_command(f"fuser -k 8000/tcp")
             log("Viewer stopped.")
        except Exception as e:
             log(f"Error stopping viewer: {e}")
        finally:
             self.view.set_status('ready', "")

    def _on_tailscale_change(self, change):
        if 'tailscale_conn' in globals():
            tailscale_conn.toggle(change)

    # --- Event Handlers ---
    def _on_rasterizer_change(self, change):
        if change['new'].startswith('Accelerated'):
            self.view.cb_sparse_adam.value = True
        else:
            self.view.cb_sparse_adam.value = False

    def _on_depth_change(self, change):
        if change['new']:
            self.view.txt_depth_path.layout.display = 'flex'
        else:
            self.view.txt_depth_path.layout.display = 'none'

    def _on_datasource_change(self, change):
        val = change['new']
        if val in ['Google Drive', 'Local Folder']:
            self.view.txt_source_path.layout.display = 'flex'
            self.view.btn_browse.layout.display = 'block'
            self.view.lbl_upload_instruction.layout.display = 'none'
        elif val == 'Upload Zip':
            self.view.txt_source_path.layout.display = 'none'
            self.view.btn_browse.layout.display = 'none'
            self.view.file_upload.layout.display = 'block'
            self.view.lbl_upload_instruction.layout.display = 'block'
        elif val == 'Custom URL':
            self.view.txt_source_path.layout.display = 'flex'
            self.view.btn_browse.layout.display = 'none'
            self.view.file_upload.layout.display = 'none'
            self.view.lbl_upload_instruction.layout.display = 'none'
        else: # Demo Data
            self.view.txt_source_path.layout.display = 'none'
            self.view.btn_browse.layout.display = 'none'
            self.view.file_upload.layout.display = 'none'
            self.view.lbl_upload_instruction.layout.display = 'none'

    # --- Browser Logic ---
    def _update_browser(self, widget_sel, widget_lbl, path):
        try:
            if not os.path.exists(path): path = '/content'
            items = sorted(os.listdir(path))
            formatted_items = []
            for item in items:
                if os.path.isdir(os.path.join(path, item)):
                    formatted_items.append(f"\ud83d\udcc2 {item}")
                else:
                    formatted_items.append(f"\ud83d\udcc4 {item}")
            widget_sel.options = formatted_items
            widget_lbl.value = f"Current: {path}"
        except Exception as e:
            widget_lbl.value = f"Error: {e}"

    def _on_up(self, widget_sel, widget_lbl, is_viewer=False):
        if is_viewer:
             self.current_path_v = os.path.dirname(self.current_path_v)
             self._update_browser(widget_sel, widget_lbl, self.current_path_v)
        else:
             self.current_path = os.path.dirname(self.current_path)
             self._update_browser(widget_sel, widget_lbl, self.current_path)

    def _on_select_item(self, change, widget_sel, widget_lbl, is_viewer=False):
        if change['new']:
            name = change['new'].split(' ', 1)[1]
            if is_viewer:
                full_path = os.path.join(self.current_path_v, name)
                if os.path.isdir(full_path):
                     self.current_path_v = full_path
                     self._update_browser(widget_sel, widget_lbl, self.current_path_v)
            else:
                full_path = os.path.join(self.current_path, name)
                if os.path.isdir(full_path):
                     self.current_path = full_path
                     self._update_browser(widget_sel, widget_lbl, self.current_path)

    def _on_confirm_select(self, browse_box_widget, widget_sel, is_viewer=False):
        val = widget_sel.value
        path_to_use = self.current_path_v if is_viewer else self.current_path
        
        if val:
            name = val.split(' ', 1)[1]
            path_to_use = os.path.join(path_to_use, name)
        
        if self.active_input:
            self.active_input.value = path_to_use
        
        browse_box_widget.layout.display = 'none'
        self.active_input = None

    def _open_browser_source(self, target_widget, title="Select File"):
        self.active_input = target_widget
        self.view.lbl_browser_title.value = f"Selecting: {title}"
        self.view.browser_box.layout.display = 'block'
        self.view.browser_box_viewer.layout.display = 'none' # Ensure other is closed
        self._update_browser(self.view.sel_files, self.view.lbl_path, self.current_path)

    def _open_browser_viewer(self, target_widget, title="Select Viewer File"):
        self.active_input = target_widget
        self.view.lbl_browser_title_v.value = f"Selecting: {title}"
        self.view.browser_box_viewer.layout.display = 'block'
        self.view.browser_box.layout.display = 'none' # Ensure other is closed
        self._update_browser(self.view.sel_files_v, self.view.lbl_path_v, self.current_path_v)

    def _on_cancel_browser(self, browse_box_widget):
        browse_box_widget.layout.display = 'none'
        self.active_input = None
"""

def patch_notebook():
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb_data = json.load(f)
    
    modified = False
    
    for cell in nb_data['cells']:
        if cell['cell_type'] == 'code':
            source_list = cell['source']
            source_str = "".join(source_list)
            
            # Patch StartViewer
            if "def start_viewer(b):" in source_str:
                print("Found StartViewer cell. Patching...")
                # Split usage lines for JSON format
                new_lines = [line + '\n' for line in new_start_viewer_source.split('\n')]
                # Remove last newline from last item if needed, but split keeps it cleaner
                new_lines = [l for l in new_lines]
                 # fix last line double newline if any
                if new_lines[-1] == '\n': new_lines.pop()
                
                cell['source'] = new_lines
                modified = True
            
            # Patch GUIController
            if "class GUIController:" in source_str:
                print("Found GUIController cell. Patching...")
                new_lines = [line + '\n' for line in new_gui_controller_source.split('\n')]
                if new_lines[-1] == '\n': new_lines.pop()
                
                cell['source'] = new_lines
                modified = True
    
    if modified:
        with open(nb_path, 'w', encoding='utf-8') as f:
            json.dump(nb_data, f, indent=2)
        print("Notebook patched successfully.")
    else:
        print("Target cells not found.")

if __name__ == "__main__":
    patch_notebook()
