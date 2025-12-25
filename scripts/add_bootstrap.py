
import json

nb_path = "gaussian_splatting_colab.ipynb"

with open(nb_path, "r") as f:
    nb = json.load(f)

# Helper to find cell by ID
def find_cell(nb, cell_id):
    for cell in nb['cells']:
        if cell.get('metadata', {}).get('id') == cell_id:
            return cell
    return None

# We need to insert a bootstrap cell BEFORE the "Key Imports" or "Action Defs".
# The ideal place is right after the "Open In Colab" badge (index 0).

bootstrap_source = [
    "# @title 0. Bootstrap (Clone Scripts)\n",
    "# ===========================\n",
    "# Clone this repo to get the 'scripts/' folder\n",
    "# ===========================\n",
    "import os\n",
    "import shutil\n",
    "\n",
    "repo_url = \"https://github.com/FutoshiNakamura-Tts/gaussian-splatting-colab\"\n",
    "branch = \"colab-t4-2025-12-18\" # Or main\n",
    "target_dir = \"/content/gaussian-splatting-colab\"\n",
    "\n",
    "if not os.path.exists(f\"{target_dir}/scripts\"):\n",
    "    print(f\"Cloning {repo_url}...\")\n",
    "    !git clone -b {branch} {repo_url} {target_dir}\n",
    "    \n",
    "    # Move scripts to current working dir root for easy access or add to path\n",
    "    # The notebook assumes scripts/ is relative to CWD.\n",
    "    # Usually Colab CWD is /content.\n",
    "    # So we should copy /content/gaussian-splatting-colab/scripts -> /content/scripts\n",
    "    if os.path.exists(f\"{target_dir}/scripts\"):\n",
    "        if os.path.exists(\"/content/scripts\"):\n",
    "            shutil.rmtree(\"/content/scripts\")\n",
    "        shutil.copytree(f\"{target_dir}/scripts\", \"/content/scripts\")\n",
    "        print(\"Scripts setup complete.\")\n",
    "    else:\n",
    "        print(\"Error: scripts folder not found in repo.\")\n",
    "else:\n",
    "    print(\"Repo already cloned. Updating scripts...\")\n",
    "    !git -C {target_dir} pull\n",
    "    if os.path.exists(\"/content/scripts\"):\n",
    "        shutil.rmtree(\"/content/scripts\")\n",
    "    shutil.copytree(f\"{target_dir}/scripts\", \"/content/scripts\")\n",
    "    print(\"Scripts updated.\")\n"
]

bootstrap_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {
        "id": "bootstrap-scripts"
    },
    "outputs": [],
    "source": bootstrap_source
}

# Insert at index 1 (after markdown header)
nb['cells'].insert(1, bootstrap_cell)

with open(nb_path, "w") as f:
    json.dump(nb, f, indent=2)

print("Added bootstrap cell to clone scripts.")
