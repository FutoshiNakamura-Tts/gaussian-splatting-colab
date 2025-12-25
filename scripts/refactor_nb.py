
import json
import os

nb_path = "gaussian_splatting_colab.ipynb"

with open(nb_path, "r") as f:
    nb = json.load(f)

# Helper to find cell by ID
def find_cell(nb, cell_id):
    for cell in nb['cells']:
        if cell.get('metadata', {}).get('id') == cell_id:
            return cell
    return None

def set_cell_source(cell, source_lines):
    # Ensure lines end with \n
    source = [line + "\n" if not line.endswith("\n") else line for line in source_lines]
    cell['source'] = source

# --- Refactoring Content ---

# 1. Action Defs: Env & Deps
source_env = [
    "# @title 3. Define Actions",
    "import shlex",
    "",
    "def setup_env(b):",
    "    out.clear_output()",
    "    run_command(f\"{sys.executable} scripts/setup_env.py\")",
    "",
    "def install_deps(b):",
    "    out.clear_output()",
    "    accel_flag = \"\"",
    "    if 'dd_rasterizer' in globals() and dd_rasterizer.value.startswith('Accelerated'):",
    "        accel_flag = \"--accelerated\"",
    "    run_command(f\"{sys.executable} scripts/install_deps.py {accel_flag}\")"
]

# 2. Action Defs: Data
source_data = [
    "def prepare_data(b):",
    "    out.clear_output()",
    "    source_type = dd_datasource.value if 'dd_datasource' in globals() else \"Demo Data\"",
    "    path = txt_source_path.value if 'txt_source_path' in globals() else \"\"",
    "    ",
    "    # Handle Upload",
    "    if source_type == 'Upload Zip':",
    "        if 'file_upload_widget' in globals() and file_upload_widget.value:",
    "            # Normalize upload content (Colab/ipywidgets variations)",
    "            vals = file_upload_widget.value",
    "            content = None",
    "            name = \"upload.zip\"",
    "            if isinstance(vals, dict): # Old style or Dict",
    "                 # Usually {name: {content: b''}}",
    "                 for k, v in vals.items():",
    "                     content = v['content']",
    "                     name = k",
    "                     break",
    "            elif isinstance(vals, (list, tuple)):",
    "                 if vals: content = vals[0]['content']; name = vals[0]['name']",
    "            ",
    "            if content:",
    "                if isinstance(content, memoryview): content = content.tobytes()",
    "                with open(name, 'wb') as f: f.write(content)",
    "                source_type = \"File Path\"",
    "                path = name",
    "            else:",
    "                log(\"No file content found in widget.\")",
    "                return",
    "        else:",
    "            log(\"Please upload a file first.\")",
    "            return",
    "            ",
    "    cmd = f\"{sys.executable} scripts/prepare_data.py --source {shlex.quote(source_type)}\"",
    "    if path: cmd += f\" --path {shlex.quote(path)}\"",
    "    run_command(cmd)"
]

# 3. Action Defs: Train
source_train = [
    "def start_training(b):",
    "    out.clear_output()",
    "    # Gather Params",
    "    src = Source_Path",
    "    out_path = Output_Path",
    "    # ... (Add logic to update Source_Path from GUI if needed, usually they modify globals or we read widgets)",
    "    # But in Cell 4.1 'Main Execution', we export widgets to globals.",
    "    # Let's read widgets directly if available.",
    "    ",
    "    args = []",
    "    args.append(f\"--source_path {shlex.quote(src)}\")",
    "    args.append(f\"--output_path {shlex.quote(out_path)}\")",
    "    args.append(f\"--iterations {Iterations}\")",
    "    args.append(f\"--sh_degree {SH_Degree}\")",
    "    if White_Background: args.append(\"--white_background\")",
    "    if Eval_Mode: args.append(\"--eval\")",
    "    ",
    "    # Widget Params",
    "    if 'cb_antialiasing' in globals() and cb_antialiasing.value: args.append(\"--antialiasing\")",
    "    if 'cb_exposure' in globals() and cb_exposure.value: args.append(\"--exposure\")",
    "    if 'cb_depth' in globals() and cb_depth.value: ",
    "        args.append(\"--depth\")",
    "        if 'txt_depth_path' in globals() and txt_depth_path.value:",
    "             args.append(f\"--depth_path {shlex.quote(txt_depth_path.value)}\")",
    "    if 'cb_sparse_adam' in globals() and cb_sparse_adam.value: args.append(\"--sparse_adam\")",
    "    if 'cb_dryrun' in globals() and cb_dryrun.value: args.append(\"--dry_run\")",
    "    ",
    "    # Transfer Params",
    "    if 'drive' in sys.modules and os.path.exists('/content/drive'):",
    "         # Maybe auto-backup to a folder with same name in Drive?",
    "         # For now, just prompt or use default. Script handle it?",
    "         # Let's check if the user set a destination in GUI? Currently no specific widget for dest.",
    "         # We'll rely on script default or logic.",
    "         pass",
    "         ",
    "    # Tailscale Logic for Transfer",
    "    # We need a widget for 'Tailscale Target Host'. ",
    "    # We should add this widget in the GUI section (later refactor step) or just rely on hardcode/notebook var.",
    "    # For now, let's assume valid notebook variable 'Tailscale_Target' if set.",
    "    if 'Tailscale_Target' in globals() and Tailscale_Target:",
    "         args.append(f\"--tailscale_target {shlex.quote(Tailscale_Target)}\")",
    "    ",
    "    full_cmd = f\"{sys.executable} scripts/train.py \" + \" \".join(args)",
    "    run_command(full_cmd)"
]

# 4. Action Defs: Viewer
source_viewer = [
    "def start_viewer(b):",
    "    out.clear_output()",
    "    ",
    "    ply = \"\"",
    "    if 'txt_viewer_path' in globals() and txt_viewer_path.value: ply = txt_viewer_path.value",
    "    ",
    "    port = 8000",
    "    cmd = f\"{sys.executable} scripts/start_viewer.py --port {port}\"",
    "    if ply: cmd += f\" --ply_file {shlex.quote(ply)}\"",
    "    # Pass output path for auto-detection",
    "    if Output_Path: cmd += f\" --output_path {shlex.quote(Output_Path)}\"",
    "    ",
    "    # Run script (it spawns server)",
    "    run_command(cmd)",
    "    ",
    "    # Handle Embedding",
    "    from google.colab import output",
    "    from google.colab.output import eval_js",
    "    from IPython.display import IFrame, display",
    "    ",
    "    if 'cb_embedded' in globals() and cb_embedded.value:",
    "        try:",
    "            proxy_base = eval_js(f\"google.colab.kernel.proxyPort({port})\")",
    "            if proxy_base:",
    "                viewer_url = f\"{proxy_base}/index.html\"",
    "                # If specific file was loaded, the script symlinked it to input.ply",
    "                # So we just open the viewer. ",
    "                # If we want to point to a specific URL param, we can, but script handles input.ply default.",
    "                ",
    "                with out_viewer:",
    "                    out_viewer.clear_output()",
    "                    display(IFrame(src=viewer_url, width='100%', height='600'))",
    "        except Exception as e:",
    "            log(f\"Embedding failed: {e}\")"
]

# Apply Changes
cell_env = find_cell(nb, 'action-defs-env')
if cell_env: set_cell_source(cell_env, source_env)

cell_data = find_cell(nb, 'action-defs-data')
if cell_data: set_cell_source(cell_data, source_data)

cell_train = find_cell(nb, 'action-defs-train')
if cell_train: set_cell_source(cell_train, source_train)

cell_viewer = find_cell(nb, 'action-defs-viewer')
if cell_viewer: set_cell_source(cell_viewer, source_viewer)

# Save
with open(nb_path, "w") as f:
    json.dump(nb, f, indent=2)

print("Notebook refactored successfully.")
