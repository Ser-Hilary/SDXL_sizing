# Made by Davemane42#0042 for ComfyUI
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

from .WaveNodes import Lerp, SinWave, InvSinWave, CosWave, InvCosWave, SquareWave, SawtoothWave, TriangleWave, AbsCosWave, AbsSinWave
from .ScheduledNodes import ValueSchedule, PromptSchedule, PromptScheduleNodeFlow, PromptScheduleNodeFlowEnd #, PromptScheduleGLIGEN

NODE_CLASS_MAPPINGS = {
    "Lerp": Lerp,
    "SinWave": SinWave,
    "InvSinWave": InvSinWave,
    "CosWave": CosWave,
    "InvCosWave": InvCosWave,
    "SquareWave":SquareWave,
    "SawtoothWave": SawtoothWave,
    "TriangleWave": TriangleWave,
    "AbsCosWave": AbsCosWave,
    "AbsSinWave": AbsSinWave,
    "PromptSchedule": PromptSchedule,
    "ValueSchedule": ValueSchedule,
    "PromptScheduleNodeFlow": PromptScheduleNodeFlow,
    "PromptScheduleNodeFlowEnd": PromptScheduleNodeFlowEnd,
    #"PromptScheduleGLIGEN": PromptScheduleGLIGEN,
}

print('\033[34mFizzleDorf Custom Nodes: \033[92mLoaded\033[0m')