
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
    source = [line + "\n" if not line.endswith("\n") else line for line in source_lines]
    cell['source'] = source

cell_train = find_cell(nb, 'action-defs-train')
if cell_train:
    # Read existing source to modify it, or just overwrite with corrected logic.
    # We want to change how Tailscale_Target is read.
    source = cell_train['source']
    new_source = []
    for line in source:
        if "if 'Tailscale_Target' in globals() and Tailscale_Target:" in line:
            new_source.append("    # Read dynamic value from widget if available\n")
            new_source.append("    ts_target = \"\"\n")
            new_source.append("    if 'txt_tailscale_target' in globals():\n")
            new_source.append("        ts_target = txt_tailscale_target.value\n")
            new_source.append("    elif 'Tailscale_Target' in globals():\n")
            new_source.append("        ts_target = Tailscale_Target\n")
            new_source.append("        \n")
            new_source.append("    if ts_target:\n")
            new_source.append("         args.append(f\"--tailscale_target {shlex.quote(ts_target)}\")\n")
        elif "args.append(f\"--tailscale_target" in line:
            pass # Skip, handled above
        else:
            new_source.append(line)
    
    cell_train['source'] = new_source

with open(nb_path, "w") as f:
    json.dump(nb, f, indent=2)

print("Train action updated for dynamic widget.")
