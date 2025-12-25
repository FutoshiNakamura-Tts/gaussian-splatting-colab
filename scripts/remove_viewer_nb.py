
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

# 1. Remove Action Defs Viewer Cell completely?
# Easier to just empty it or find it and delete the cell object from list.
nb['cells'] = [c for c in nb['cells'] if c.get('metadata', {}).get('id') != 'action-defs-viewer']

# 2. Cleanup GUI Layout (View)
# Filter out lines containing viewer widgets
gui_view_patterns = [
    r"self\.txt_viewer_path",
    r"self\.cb_embedded",
    r"self\.btn_browse_viewer",
    r"self\.btn_view",
    r"self\.btn_stop_viewer",
    r"self\.out_viewer",
    r"widgets\.Label\(\"Viewer Config:\"\)",
    r"self\.browser_box_viewer",
    # Remove container lines that add these
    r"widgets\.HBox\(\[self\.txt_viewer",
    r"widgets\.HBox\(\[self\.cb_embedded",
    r"widgets\.HBox\(\[self\.btn_view",
    r"out_viewer,"
]
# Also need to remove the browser definition block for viewer
# We can use block removal for that.
view_cell = next((c for c in nb['cells'] if c.get('metadata', {}).get('id') == 'action-defs-gui-layout'), None)
modify_cell(view_cell, gui_view_patterns, block_removal_start="# File Browser Widgets (Viewer)", block_removal_end="self.browser_box_viewer.layout.display = 'none'")


# 3. Cleanup GUI Controller (Logic)
gui_ctrl_patterns = [
    r"self\.current_path_v",
    r"self\.view\.sel_files_v",
    r"self\.view\.btn_browse_viewer",
    r"self\.view\.btn_view",
    r"self\.view\.btn_stop_viewer",
    r"start_viewer",
    r"stop_viewer",
    r"is_viewer=True", # Remove args in calls
    r"self\._open_browser_viewer",
    r"self\.view\.browser_box_viewer",
    r"self\.view\.btn_cancel_browser_v",
    r"self\.view\.btn_select_v",
    r"self\.view\.btn_up_v"
]
ctrl_cell = next((c for c in nb['cells'] if c.get('metadata', {}).get('id') == 'action-defs-gui-controller'), None)

# Controller is tricky because of multi-line methods.
# Let's simple remove lines with these keywords.
# For `is_viewer=True` logic inside methods, removing the `if is_viewer:` block is hard with line filtering.
# We might need to just rewrite the Controller cell entirely or accept some dead code.
# But actually, the `_on_up` method has `if is_viewer: ... else: ...`.
# If we remove lines with `is_viewer`, we might break the if/else structure indentation.
# 
# Safer approach for Controller: Replace the cell with a clean version without viewer logic.
# Since we have the clean "Frontend-Only" code in mind, let's write strict content.

clean_controller_source = [
    "# @title 4.2. GUI Controller (Logic)\n",
    "# ===========================\n",
    "# Event binding and Logic\n",
    "# ===========================\n",
    "import os\n",
    "\n",
    "class GUIController:\n",
    "    def __init__(self, view):\n",
    "        self.view = view\n",
    "        self.current_path = os.getcwd()\n",
    "        self.active_input = None\n",
    "        \n",
    "        # Init browsers\n",
    "        self._update_browser(self.view.sel_files, self.view.lbl_path, self.current_path)\n",
    "\n",
    "        # Bind events last to ensure all methods are defined\n",
    "        self._bind_events()\n",
    "\n",
    "    def _bind_events(self):\n",
    "        # Tailscale\n",
    "        if 'tailscale_conn' in globals():\n",
    "            self.view.cb_tailscale.observe(self._on_tailscale_change, names='value')\n",
    "            tailscale_conn.status_callback = lambda msg: setattr(self.view.lbl_tailscale_status, 'value', msg)\n",
    "        \n",
    "        # Visibility Logic\n",
    "        self.view.dd_rasterizer.observe(self._on_rasterizer_change, names='value')\n",
    "        self.view.cb_depth.observe(self._on_depth_change, names='value')\n",
    "        self.view.dd_datasource.observe(self._on_datasource_change, names='value')\n",
    "        \n",
    "        # File Browser (Source)\n",
    "        self.view.btn_browse.on_click(lambda b: self._open_browser_source(self.view.txt_source_path, \"Source Path\"))\n",
    "        self.view.btn_up.on_click(lambda b: self._on_up(self.view.sel_files, self.view.lbl_path))\n",
    "        self.view.sel_files.observe(lambda change: self._on_select_item(change, self.view.sel_files, self.view.lbl_path), names='value')\n",
    "        self.view.btn_select.on_click(lambda b: self._on_confirm_select(self.view.browser_box, self.view.sel_files))\n",
    "        self.view.btn_cancel_browser.on_click(lambda b: self._on_cancel_browser(self.view.browser_box))\n",
    "\n",
    "        # Actions with Async Feedback\n",
    "        self.view.btn_env.on_click(lambda b: self._run_action(\"Setting up Env...\", setup_env))\n",
    "        self.view.btn_deps.on_click(lambda b: self._run_action(\"Installing Deps...\", install_deps))\n",
    "        self.view.btn_data.on_click(lambda b: self._run_action(\"Preparing Data...\", prepare_data))\n",
    "        self.view.btn_train.on_click(lambda b: self._run_action(\"Training...\", start_training))\n",
    "\n",
    "    def _run_action(self, msg, func):\n",
    "        self.view.set_status('busy', msg)\n",
    "        for w in self.view.lockable_widgets:\n",
    "            w.disabled = True\n",
    "\n",
    "        try:\n",
    "            func(None)\n",
    "        except Exception as e:\n",
    "            log(f\"Error: {e}\")\n",
    "        finally:\n",
    "            self.view.set_status('ready', \"\")\n",
    "            for w in self.view.lockable_widgets:\n",
    "                w.disabled = False\n",
    "    \n",
    "    def _on_tailscale_change(self, change):\n",
    "        if 'tailscale_conn' in globals():\n",
    "            tailscale_conn.toggle(change)\n",
    "\n",
    "    # --- Event Handlers ---\n",
    "    def _on_rasterizer_change(self, change):\n",
    "        if change['new'].startswith('Accelerated'):\n",
    "            self.view.cb_sparse_adam.value = True\n",
    "        else:\n",
    "            self.view.cb_sparse_adam.value = False\n",
    "\n",
    "    def _on_depth_change(self, change):\n",
    "        if change['new']:\n",
    "            self.view.txt_depth_path.layout.display = 'flex'\n",
    "        else:\n",
    "            self.view.txt_depth_path.layout.display = 'none'\n",
    "\n",
    "    def _on_datasource_change(self, change):\n",
    "        val = change['new']\n",
    "        if val in ['Google Drive', 'Local Folder']:\n",
    "            self.view.txt_source_path.layout.display = 'flex'\n",
    "            self.view.btn_browse.layout.display = 'block'\n",
    "            self.view.lbl_upload_instruction.layout.display = 'none'\n",
    "        elif val == 'Upload Zip':\n",
    "            self.view.txt_source_path.layout.display = 'none'\n",
    "            self.view.btn_browse.layout.display = 'none'\n",
    "            self.view.file_upload.layout.display = 'block'\n",
    "            self.view.lbl_upload_instruction.layout.display = 'block'\n",
    "        elif val == 'Custom URL':\n",
    "            self.view.txt_source_path.layout.display = 'flex'\n",
    "            self.view.btn_browse.layout.display = 'none'\n",
    "            self.view.file_upload.layout.display = 'none'\n",
    "            self.view.lbl_upload_instruction.layout.display = 'none'\n",
    "        else: # Demo Data\n",
    "            self.view.txt_source_path.layout.display = 'none'\n",
    "            self.view.btn_browse.layout.display = 'none'\n",
    "            self.view.file_upload.layout.display = 'none'\n",
    "            self.view.lbl_upload_instruction.layout.display = 'none'\n",
    "\n",
    "    # --- Browser Logic ---\n",
    "    def _update_browser(self, widget_sel, widget_lbl, path):\n",
    "        try:\n",
    "            if not os.path.exists(path): path = '/content'\n",
    "            items = sorted(os.listdir(path))\n",
    "            formatted_items = []\n",
    "            for item in items:\n",
    "                if os.path.isdir(os.path.join(path, item)):\n",
    "                    formatted_items.append(f\"\\ud83d\\udcc2 {item}\")\n",
    "                else:\n",
    "                    formatted_items.append(f\"\\ud83d\\udcc4 {item}\")\n",
    "            widget_sel.options = formatted_items\n",
    "            widget_lbl.value = f\"Current: {path}\"\n",
    "        except Exception as e:\n",
    "            widget_lbl.value = f\"Error: {e}\"\n",
    "\n",
    "    def _on_up(self, widget_sel, widget_lbl):\n",
    "        self.current_path = os.path.dirname(self.current_path)\n",
    "        self._update_browser(widget_sel, widget_lbl, self.current_path)\n",
    "\n",
    "    def _on_select_item(self, change, widget_sel, widget_lbl):\n",
    "        if change['new']:\n",
    "            name = change['new'].split(' ', 1)[1]\n",
    "            full_path = os.path.join(self.current_path, name)\n",
    "            if os.path.isdir(full_path):\n",
    "                 self.current_path = full_path\n",
    "                 self._update_browser(widget_sel, widget_lbl, self.current_path)\n",
    "\n",
    "    def _on_confirm_select(self, browse_box_widget, widget_sel):\n",
    "        val = widget_sel.value\n",
    "        path_to_use = self.current_path\n",
    "        \n",
    "        if val:\n",
    "            name = val.split(' ', 1)[1]\n",
    "            path_to_use = os.path.join(path_to_use, name)\n",
    "        \n",
    "        if self.active_input:\n",
    "            self.active_input.value = path_to_use\n",
    "        \n",
    "        browse_box_widget.layout.display = 'none'\n",
    "        self.active_input = None\n",
    "\n",
    "    def _open_browser_source(self, target_widget, title=\"Select File\"):\n",
    "        self.active_input = target_widget\n",
    "        self.view.lbl_browser_title.value = f\"Selecting: {title}\"\n",
    "        self.view.browser_box.layout.display = 'block'\n",
    "        self._update_browser(self.view.sel_files, self.view.lbl_path, self.current_path)\n",
    "\n",
    "    def _on_cancel_browser(self, browse_box_widget):\n",
    "        browse_box_widget.layout.display = 'none'\n",
    "        self.active_input = None\n"
]

if ctrl_cell:
    ctrl_cell['source'] = clean_controller_source

# Save
with open(nb_path, "w") as f:
    json.dump(nb, f, indent=2)

print("Removed Viewer features from notebook.")
