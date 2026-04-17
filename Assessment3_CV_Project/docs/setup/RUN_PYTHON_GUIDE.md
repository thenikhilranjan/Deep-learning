# How to Run Python Files - Troubleshooting Guide

## Common Issues and Solutions

### Issue 1: File Not Found
**Error:** `python3: can't open file 'your_script.py': [Errno 2] No such file or directory`

**Solution:**
1. Make sure you're in the correct directory
2. Check if the file exists: `ls -la your_script.py`
3. Use the full path if file is elsewhere: `python3 /path/to/your_script.py`

### Issue 2: Virtual Environment Not Activated
**Error:** Missing packages or import errors

**Solution:**
Always activate the virtual environment first:
```bash
source ../venv/bin/activate
python your_script.py
```

### Issue 3: Permission Denied
**Error:** `Permission denied` when running the file

**Solution:**
Make the file executable:
```bash
chmod +x your_script.py
```

Or run with python explicitly:
```bash
python3 your_script.py
```

### Issue 4: Python Not Found
**Error:** `command not found: python3`

**Solution:**
Check Python installation:
```bash
which python3
python3 --version
```

## How to Run Python Files

### Method 1: Using python3 command
```bash
# Activate virtual environment (recommended)
source ../venv/bin/activate

# Run the file
python your_script.py
# or
python3 your_script.py
```

### Method 2: Make file executable
```bash
# Add shebang line at top of file: #!/usr/bin/env python3
chmod +x your_script.py
./your_script.py
```

### Method 3: Using full path
```bash
/Users/nikhilranjan/Desktop/Cursor/venv/bin/python your_script.py
```

## Quick Diagnostic Commands

Check if file exists:
```bash
ls -la your_script.py
```

Check Python version:
```bash
python3 --version
```

Check if virtual environment is active (you should see `(venv)` in prompt):
```bash
echo $VIRTUAL_ENV
```

Test Python execution:
```bash
python3 -c "print('Python is working!')"
```
