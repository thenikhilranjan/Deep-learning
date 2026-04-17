# Fix: ModuleNotFoundError for cv2 in Jupyter Notebook

## Problem
The notebook is not using the virtual environment where OpenCV is installed.

## ✅ Solution: Select the Correct Kernel

### Option 1: In Jupyter Notebook (Web Interface)

1. **Open your notebook** in Jupyter
2. **Click on "Kernel"** in the menu bar
3. **Select "Change Kernel"** → **"Python (venv)"** or **"Python Environments"**
4. If you don't see the venv option:
   - Select **"Select Another Kernel"**
   - Choose **"Python Environments"**
   - Select: `/Users/nikhilranjan/Desktop/Cursor/venv/bin/python`

### Option 2: In VS Code / Cursor

1. **Open your `.ipynb` file**
2. **Click on the kernel selector** (top-right corner, shows current kernel)
3. **Select "Select Another Kernel"**
4. **Choose "Python Environments"**
5. **Select:** `/Users/nikhilranjan/Desktop/Cursor/venv/bin/python`

### Option 3: Register Kernel Manually

Run this command to register the kernel:

```bash
cd /Users/nikhilranjan/Desktop/Cursor/Assessment3_CV_Project
source ../venv/bin/activate
python -m ipykernel install --user --name=venv --display-name "Python (venv)"
```

Then restart your notebook and select "Python (venv)" kernel.

## Quick Fix: Restart Kernel

After selecting the correct kernel:

1. **Restart the kernel**: Kernel → Restart Kernel (or click the restart button)
2. **Run all cells again** from the top

## Verify It's Working

Run this in a new cell to verify:

```python
import sys
print("Python path:", sys.executable)
# Should show: /Users/nikhilranjan/Desktop/Cursor/venv/bin/python

import cv2
print(f"OpenCV version: {cv2.__version__}")
# Should show: OpenCV version: 4.13.0
```

## Alternative: Install in Current Environment

If you can't change the kernel, install OpenCV in the current environment:

```python
# Run this in a notebook cell
import sys
!{sys.executable} -m pip install opencv-python
```

Then restart the kernel and try importing again.

## Still Having Issues?

1. **Check which Python is being used:**
   ```python
   import sys
   print(sys.executable)
   ```

2. **Verify OpenCV is installed:**
   ```bash
   source /Users/nikhilranjan/Desktop/Cursor/venv/bin/activate
   python -c "import cv2; print(cv2.__version__)"
   ```

3. **Reinstall OpenCV:**
   ```bash
   source /Users/nikhilranjan/Desktop/Cursor/venv/bin/activate
   pip install --upgrade opencv-python
   ```
