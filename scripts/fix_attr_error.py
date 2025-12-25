
import json
import re

nb_path = "gaussian_splatting_colab.ipynb"

with open(nb_path, "r") as f:
    nb = json.load(f)

# Helper to modify cell source
def modify_cell_remove_lines(cell, patterns):
    if not cell: return
    source = cell['source']
    new_source = []
    
    for line in source:
        is_match = False
        for pat in patterns:
            if pat in line:
                is_match = True
                break
        if not is_match:
            new_source.append(line)
            
    cell['source'] = new_source

# Patterns to remove from Main Execution
# We removed "cb_embedded" from View class, but "Main Execution" cell still tries to export it.
main_patterns = [
    "globals()['cb_embedded']",
    "view.cb_embedded",
    "globals()['txt_viewer_path']", 
    "view.txt_viewer_path"
]

main_cell = next((c for c in nb['cells'] if c.get('metadata', {}).get('id') == 'main-execution'), None)
if main_cell:
    modify_cell_remove_lines(main_cell, main_patterns)

# Also check if any Controller bindings were missed
ctrl_cell = next((c for c in nb['cells'] if c.get('metadata', {}).get('id') == 'action-defs-gui-controller'), None)
if ctrl_cell:
    # Just extra safety, though previous script should have cleaned it.
    modify_cell_remove_lines(ctrl_cell, ["cb_embedded", "txt_viewer_path"])

with open(nb_path, "w") as f:
    json.dump(nb, f, indent=2)

print("Fixed AttributeError by removing dead widget references.")
