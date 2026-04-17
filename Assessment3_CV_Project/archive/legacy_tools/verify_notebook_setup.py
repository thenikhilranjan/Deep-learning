#!/usr/bin/env python3
"""
Quick verification script to check if notebook environment is set up correctly.
Run this in a notebook cell or as a Python script.
"""

import importlib
import sys
from pathlib import Path


def get_expected_python():
    """Return the most likely venv Python path for this project."""
    script_dir = Path(__file__).resolve().parent
    local_python = script_dir / "venv" / "bin" / "python"
    parent_python = script_dir.parent / "venv" / "bin" / "python"

    if local_python.exists():
        return local_python

    return parent_python

def check_module(module_name):
    """Check if a module can be imported."""
    try:
        mod = importlib.import_module(module_name)
        if hasattr(mod, '__version__'):
            return True, mod.__version__
        return True, "installed"
    except ImportError:
        return False, None

def main():
    expected_python = get_expected_python()
    activate_command = expected_python.parent / "activate"

    print("=" * 60)
    print("Notebook Environment Verification")
    print("=" * 60)
    print()
    
    # Check Python path
    print(f"Python Executable: {sys.executable}")
    print(f"Python Version: {sys.version}")
    print()
    
    # Check if using venv
    if 'venv' in sys.executable or 'virtualenv' in sys.executable:
        print("✅ Using virtual environment")
    else:
        print("⚠️  Not using virtual environment")
        print(f"   Expected: {expected_python}")
    print()
    
    # Check required modules
    modules = {
        'cv2': 'OpenCV',
        'numpy': 'NumPy',
        'matplotlib': 'Matplotlib',
        'IPython': 'IPython',
        'jupyter': 'Jupyter',
    }
    
    print("Required Modules:")
    print("-" * 60)
    all_ok = True
    for module, name in modules.items():
        installed, version = check_module(module)
        if installed:
            print(f"✅ {name:15} {version:>20}")
        else:
            print(f"❌ {name:15} {'NOT INSTALLED':>20}")
            all_ok = False
    print()
    
    if all_ok:
        print("=" * 60)
        print("✅ All modules are installed correctly!")
        print("=" * 60)
        return 0
    else:
        print("=" * 60)
        print("❌ Some modules are missing!")
        print("=" * 60)
        print("\nTo fix:")
        print("1. Make sure you're using the correct kernel")
        print(f"2. Activate venv: source {activate_command}")
        print("3. Install missing packages: pip install opencv-python numpy matplotlib")
        return 1

if __name__ == '__main__':
    sys.exit(main())
