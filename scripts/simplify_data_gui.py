
import json
import re

nb_path = "gaussian_splatting_colab.ipynb"

with open(nb_path, "r") as f:
    nb = json.load(f)

# Helper to modify cell source
def modify_cell(cell, keyword_removal_patterns, block_removal_start=None, block_removal_end=None):
    if not cell: return
    source = cell['source']
    new_source = []
    skip = False
    
    for line in source:
        # Check start/end block
        if block_removal_start and block_removal_start in line:
            skip = True
        
        if not skip:
            # Check line patterns
            is_match = False
            for pat in keyword_removal_patterns:
                if re.search(pat, line):
                    is_match = True
                    break
            if not is_match:
                new_source.append(line)
        
        if block_removal_end and block_removal_end in line and skip:
            skip = False

    cell['source'] = new_source

# 1. Update Layout (GUIWidget)
# Remove Upload/Drive/URL specific widgets and simplify Dropdown info
layout_patterns_remove = [
    r"self\.file_upload",
    r"self\.lbl_upload_instruction",
    r"self\.btn_browse", # Browser might still be useful for selecting folder? Let's keep browser but remove Upload widget.
    # Actually, browser is useful for finding the rsync'd folder.
    r"Upload Zip", 
    r"Custom URL",
    r"Google Drive",
    r"widgets\.HBox\(\[self\.file_upload", 
]

# We want to change the Dropdown options line specifically.
# It's hard to regex replace a specific line content with generic removal logic.
# Let's iterate and modify the dropdown options line.
view_cell = next((c for c in nb['cells'] if c.get('metadata', {}).get('id') == 'action-defs-gui-layout'), None)
if view_cell:
    new_source = []
    for line in view_cell['source']:
        if "self.dd_datasource =" in line:
            # Replace options
            new_source.append("        self.dd_datasource = widgets.Dropdown(options=['Demo Data', 'User Data (Path)'], value='Demo Data', description='Data Source:', style=self.style)\n")
        elif "self.file_upload =" in line or "self.lbl_upload_instruction =" in line or "self.file_upload.layout" in line or "self.lbl_upload_instruction.layout" in line:
            pass # Remove these definition lines
        elif "widgets.HBox([self.file_upload, self.lbl_upload_instruction])," in line:
            pass # Remove container line
        else:
            new_source.append(line)
    view_cell['source'] = new_source

# 2. Update Controller (Logic)
# Remove Upload/URL logic in _on_datasource_change
ctrl_cell = next((c for c in nb['cells'] if c.get('metadata', {}).get('id') == 'action-defs-gui-controller'), None)
if ctrl_cell:
    new_source = []
    skip_block = False
    for line in ctrl_cell['source']:
        # Simplify _on_datasource_change
        if "def _on_datasource_change(self, change):" in line:
            new_source.append(line)
            new_source.append("        val = change['new']\n")
            new_source.append("        if val == 'User Data (Path)':\n")
            new_source.append("            self.view.txt_source_path.layout.display = 'flex'\n")
            new_source.append("            self.view.btn_browse.layout.display = 'block'\n")
            new_source.append("        else: # Demo Data\n")
            new_source.append("            self.view.txt_source_path.layout.display = 'none'\n")
            new_source.append("            self.view.btn_browse.layout.display = 'none'\n")
            skip_block = True
        
        if skip_block:
            # Skip until next method def
            if line.strip().startswith("def ") or line.strip().startswith("# ---"):
                skip_block = False
                new_source.append(line)
        else:
            if "self.view.file_upload.layout.display" in line or "self.view.lbl_upload_instruction.layout.display" in line:
                pass
            else:
                 new_source.append(line)
    
    ctrl_cell['source'] = new_source

# 3. Update Action Def (Data)
# Remove Upload handling logic
action_cell = next((c for c in nb['cells'] if c.get('metadata', {}).get('id') == 'action-defs-data'), None)
if action_cell:
    new_source = []
    new_source.append("def prepare_data(b):\n")
    new_source.append("    out.clear_output()\n")
    new_source.append("    source_type = dd_datasource.value if 'dd_datasource' in globals() else \"Demo Data\"\n")
    new_source.append("    path = txt_source_path.value if 'txt_source_path' in globals() else \"\"\n")
    new_source.append("    \n")
    new_source.append("    # Simple pass-through. prepare_data.py will handle validation.\n")
    new_source.append("    cmd = f\"{sys.executable} scripts/prepare_data.py --source {shlex.quote(source_type)}\"\n")
    new_source.append("    if path: cmd += f\" --path {shlex.quote(path)}\"\n")
    new_source.append("    run_command(cmd)\n")
    
    action_cell['source'] = new_source

# 4. Remove file_upload export from Main
main_cell = next((c for c in nb['cells'] if c.get('metadata', {}).get('id') == 'main-execution'), None)
if main_cell:
    main_cell['source'] = [line for line in main_cell['source'] if "file_upload_widget" not in line]

with open(nb_path, "w") as f:
    json.dump(nb, f, indent=2)

print("Simplified Data Source options in notebook.")
