import json

notebook_path = "/home/nakamura/git/gaussian-splatting-colab/gaussian_splatting_colab.ipynb"

def patch_notebook():
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # Find the cell "action-defs-viewer"
    target_cell = None
    for cell in nb['cells']:
        if cell.get('metadata', {}).get('id') == "action-defs-viewer":
            target_cell = cell
            break
    
    if not target_cell:
        print("Error: Could not find cell with id 'action-defs-viewer'")
        return

    source_lines = target_cell['source']
    
    # We will iterate and build a new source list
    new_source = []
    
    # Signatures to look for
    sig1 = '        if proxy_base:\n'
    sig1_log = '            log(f"\\\\n\\ud83c\\udf0d Public Proxy URL: {proxy_base}{viewer_path}")\n'
    # Note: JSON source lines usually keep \n
    
    sig2 = "    if 'cb_embedded' in globals() and cb_embedded.value:\n"
    sig2_log = '        log("Embedding viewer...")\n'
    
    i = 0
    while i < len(source_lines):
        line = source_lines[i]
        
        # Patch 1: Proxy Debug
        if line == sig1 and (i+1 < len(source_lines)) and source_lines[i+1] == sig1_log:
            new_source.append(line)
            new_source.append(source_lines[i+1])
            new_source.append('            log(f"[DEBUG] Proxy Base: {proxy_base}")\n')
            new_source.append('        else:\n')
            new_source.append('            log("[DEBUG] Proxy Base not found (eval_js returned None)")\n')
            i += 2 # Skip original if and log
            continue

        # Patch 2: Embed Debug
        if line == sig2 and (i+1 < len(source_lines)) and source_lines[i+1] == sig2_log:
            new_source.append(line)
            new_source.append(source_lines[i+1])
            new_source.append('        log(f"[DEBUG] Calling serve_kernel_port_as_iframe(port={port}, path=\'{viewer_path}\', height=600)")\n')
            i += 2
            continue
            
        new_source.append(line)
        i += 1
        
    target_cell['source'] = new_source
    
    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=2)
    
    print("Notebook patched successfully.")

if __name__ == "__main__":
    patch_notebook()
