#!/bin/bash

# Quick Start Script for Jupyter Notebooks
# This script activates the virtual environment and starts Jupyter

echo "🚀 Starting Jupyter Notebook Environment..."
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Prefer a local venv if present, otherwise use the repo-level venv.
LOCAL_VENV="$SCRIPT_DIR/venv"
PARENT_VENV="$SCRIPT_DIR/../venv"

if [ -d "$LOCAL_VENV" ]; then
    VENV_DIR="$LOCAL_VENV"
elif [ -d "$PARENT_VENV" ]; then
    VENV_DIR="$PARENT_VENV"
else
    echo "❌ Error: Could not find a virtual environment"
    echo "   Checked: $LOCAL_VENV"
    echo "   Checked: $PARENT_VENV"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Error: Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"
echo ""

# Launch Jupyter from the project folder so notebook-relative files resolve.
cd "$SCRIPT_DIR" || exit 1

# Display Python and package versions
echo "📊 Environment Info:"
python --version
echo "Jupyter: $(jupyter --version 2>/dev/null | head -1)"
echo ""

# Ask user which interface to use
echo "Which interface would you like to use?"
echo "1) Jupyter Notebook (classic)"
echo "2) JupyterLab (modern)"
read -p "Enter choice [1 or 2] (default: 1): " choice

case $choice in
    2)
        echo "🚀 Starting JupyterLab..."
        jupyter lab
        ;;
    *)
        echo "🚀 Starting Jupyter Notebook..."
        jupyter notebook
        ;;
esac
