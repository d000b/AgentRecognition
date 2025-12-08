
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Tuple

def check_python_packages():
    print(os.system("python -m pip freeze"))


check_python_packages()
