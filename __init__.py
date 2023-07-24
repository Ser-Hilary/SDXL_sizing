import os
import subprocess
import importlib.util
import sys

import __main__

python = sys.executable

def is_installed(package, package_overwrite=None):
    try:
        spec = importlib.util.find_spec(package)
    except ModuleNotFoundError:
        pass

    package = package_overwrite or package

    if spec is None:
        print(f"Installing {package}...")
        command = f'"{python}" -m pip install {package}'
  
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, env=os.environ)

        if result.returncode != 0:
            print(f"Couldn't install\nCommand: {command}\nError code: {result.returncode}")

from .conditioning_sizing_for_SDXL import sizing_node, sizing_node_basic

NODE_CLASS_MAPPINGS = {
    "sizing_node": sizing_node,
    "sizing_node_basic": sizing_node_basic

}
NODE_DISPLAY_NAME_MAPPINGS = {
    "sizing_node": "sizing for SDXL (advanced)",
    "sizing_node_basic": "sizing for SDXL"
}

print('\033[34mSer-Hilary Custom Nodes: \033[92mLoaded\033[0m')
