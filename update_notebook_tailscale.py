import json

notebook_path = "/home/nakamura/git/gaussian-splatting-colab/gaussian_splatting_colab.ipynb"

def patch_notebook():
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # Find the cell "action-defs-tailscale"
    target_cell = None
    for cell in nb['cells']:
        if cell.get('metadata', {}).get('id') == "action-defs-tailscale":
            target_cell = cell
            break
    
    if not target_cell:
        print("Error: Could not find cell with id 'action-defs-tailscale'")
        return

    source_lines = target_cell['source']
    
    # We will iterate and build a new source list
    new_source = []
    
    # Signature
    sig1 = '        self.log("Tailscale Connected (check output for login link if needed).")\n'
    
    i = 0
    patched = False
    while i < len(source_lines):
        line = source_lines[i]
        
        new_source.append(line)
        
        if line == sig1 and not patched:
             # Add debug logs
             new_source.append('        self.log("[DEBUG] Verifying connection...")\n')
             new_source.append('        run_command("tailscale status")\n')
             patched = True
        
        i += 1
        
    target_cell['source'] = new_source
    
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    
    if patched:
        print("Tailscale logic patched successfully.")
    else:
        print("Warning: Tailscale signature not found.")

if __name__ == "__main__":
    patch_notebook()
