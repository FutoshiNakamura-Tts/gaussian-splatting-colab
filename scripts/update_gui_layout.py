
import json
import os

nb_path = "gaussian_splatting_colab.ipynb"

with open(nb_path, "r") as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell.get('metadata', {}).get('id') == 'action-defs-gui-layout':
        source = cell['source']
        # We need to insert the new widget definition and add it to the container.
        # This is a bit fragile with string manipulation, but we'll try to find anchors.
        
        # 1. Add Widget Definition
        # Find: self.cb_tailscale = ...
        # Insert after: self.txt_tailscale_target = widgets.Text(description='Target Device:', placeholder='e.g. mypc', style=self.style)
        
        new_source = []
        widget_added = False
        container_added = False
        
        for line in source:
            new_source.append(line)
            if "self.cb_tailscale = " in line and not widget_added:
                new_source.append("        self.txt_tailscale_target = widgets.Text(value='', placeholder='Hostname (e.g. mypc) for File Drop', description='Target Device:', style=self.style)\n")
                widget_added = True
            
            # 2. Add to Container
            # Find: widgets.HBox([self.cb_tailscale, self.lbl_tailscale_status]),
            # Replace with: widgets.HBox([self.cb_tailscale, self.lbl_tailscale_status, self.txt_tailscale_target]),
            if "widgets.HBox([self.cb_tailscale, self.lbl_tailscale_status])" in line and not container_added:
                 # Remove last added line (the original hbox)
                 new_source.pop() 
                 new_source.append("            widgets.HBox([self.cb_tailscale, self.lbl_tailscale_status, self.txt_tailscale_target]),\n")
                 container_added = True

        cell['source'] = new_source
        
    if cell.get('metadata', {}).get('id') == 'main-execution':
        # Export the new widget to globals
        source = cell['source']
        new_source = []
        export_added = False
        for line in source:
            new_source.append(line)
            if "globals()['cb_tailscale'] = view.cb_tailscale" in line and not export_added:
                new_source.append("    globals()['Tailscale_Target'] = view.txt_tailscale_target.value # Initial value usually empty, but we bind it?\n")
                new_source.append("    # Note: text widgets need to be accessed via value at runtime usually, but our refactor code reads globals().\n")
                new_source.append("    # To make 'Tailscale_Target' dynamic, we should likely read view.txt_tailscale_target.value INSIDE the action function.\n")
                new_source.append("    # But our refactor_nb.py assumed globals(). Let's fix main execution to NOT export static value but maybe we can just alias the widget if we want.\n")
                new_source.append("    # Actually, the action function `start_training` in refactor_nb.py checks `if 'Tailscale_Target' in globals()`.\n")
                new_source.append("    # If we want it to be dynamic, we should alias the WIDGET to a global name, then read .value.\n")
                new_source.append("    globals()['txt_tailscale_target'] = view.txt_tailscale_target\n")
                export_added = True
        
        cell['source'] = new_source

with open(nb_path, "w") as f:
    json.dump(nb, f, indent=2)

print("GUI Layout updated.")
