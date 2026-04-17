# Jupyter Notebook Environment Setup Guide

## ✅ Installation Complete!

Your Python environment is now ready for Jupyter notebooks with all required packages installed.

## Installed Packages

- **Jupyter Notebook** - Interactive notebook environment
- **IPython** - Enhanced Python shell
- **NumPy** - Numerical computing
- **Matplotlib** - Data visualization
- **OpenCV** - Computer vision library
- **Pillow** - Image processing
- **IPykernel** - Jupyter kernel support

## How to Use

### Option 1: Launch Jupyter Notebook (Recommended)

```bash
# Navigate to your project directory
cd /Users/nikhilranjan/Desktop/Cursor/Assessment3_CV_Project

# Activate the repo-level virtual environment
source ../venv/bin/activate

# Launch Jupyter Notebook
jupyter notebook
```

This will:
- Start a Jupyter server
- Open your web browser automatically
- Allow you to create and edit `.ipynb` files

### Option 2: Launch JupyterLab (Modern Interface)

```bash
# Activate the repo-level virtual environment
source ../venv/bin/activate

# Launch JupyterLab
jupyter lab
```

### Option 3: Use in VS Code / Cursor

1. Open your `.ipynb` file in Cursor/VS Code
2. Select the Python kernel:
   - Click on the kernel selector (top-right)
   - Choose "Python (venv)" or the virtual environment
   - If not listed, select "Select Another Kernel" → "Python Environments"
   - Choose the interpreter: `/Users/nikhilranjan/Desktop/Cursor/venv/bin/python`

## Running Your Notebooks

### For `Week2-Lab2-EdgeDetection-AWS.ipynb`:
```bash
cd /Users/nikhilranjan/Desktop/Cursor/Assessment3_CV_Project
source /Users/nikhilranjan/Desktop/Cursor/venv/bin/activate
jupyter notebook Week2-Lab2-EdgeDetection-AWS.ipynb
```

### For `Week2-Lab2-MachineLearning-AWS.ipynb`:
```bash
cd /Users/nikhilranjan/Desktop/Cursor/Assessment3_CV_Project
source /Users/nikhilranjan/Desktop/Cursor/venv/bin/activate
jupyter notebook Week2-Lab2-MachineLearning-AWS.ipynb
```

## Verify Installation

Run this in a Python cell to verify everything works:

```python
import cv2
import numpy as np
import matplotlib.pyplot as plt
import IPython

print(f"✅ OpenCV: {cv2.__version__}")
print(f"✅ NumPy: {np.__version__}")
print(f"✅ Matplotlib: {plt.matplotlib.__version__}")
print(f"✅ IPython: {IPython.__version__}")
```

## Troubleshooting

### Issue: Kernel not found in Jupyter
**Solution:** Register the kernel manually:
```bash
source ../venv/bin/activate
python -m ipykernel install --user --name=venv --display-name "Python (venv)"
```

### Issue: Packages not found in notebook
**Solution:** 
1. Make sure virtual environment is activated
2. Select the correct kernel in Jupyter
3. Restart the kernel: Kernel → Restart Kernel

### Issue: Permission errors
**Solution:** The kernel registration may require user permissions. You can:
- Run Jupyter from the activated virtual environment (it will use the venv Python)
- Or manually register kernel with appropriate permissions

## Quick Start Commands

```bash
# Activate environment from the project folder
source ../venv/bin/activate

# Start Jupyter
jupyter notebook

# Or start JupyterLab
jupyter lab

# Stop server: Press Ctrl+C in terminal
```

## File Locations

- **Project Folder:** `/Users/nikhilranjan/Desktop/Cursor/Assessment3_CV_Project/`
- **Virtual Environment:** `/Users/nikhilranjan/Desktop/Cursor/venv/`
- **Requirements File:** `/Users/nikhilranjan/Desktop/Cursor/Assessment3_CV_Project/requirements_jupyter.txt`
- **Python Executable:** `/Users/nikhilranjan/Desktop/Cursor/venv/bin/python`

## Next Steps

1. ✅ Environment is ready
2. ✅ All packages installed
3. 🚀 Launch Jupyter and start coding!

Enjoy working with your notebooks! 🎉
