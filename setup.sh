#!/bin/bash

# Development Environment Setup Script
# This script helps set up your Python development environment

echo "🔍 Checking development environment..."

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python 3 found: $(python3 --version)"
else
    echo "❌ Python 3 not found"
    exit 1
fi

# Check Xcode Command Line Tools
if xcode-select -p &> /dev/null; then
    echo "✅ Xcode Command Line Tools installed"
else
    echo "⚠️  Xcode Command Line Tools not found"
    echo "   Please run: xcode-select --install"
    echo "   Or download from: https://developer.apple.com/download/all/"
    exit 1
fi

# Check pip
if command -v pip3 &> /dev/null; then
    echo "✅ pip3 found: $(pip3 --version)"
else
    echo "⚠️  pip3 not found, attempting to install..."
    python3 -m ensurepip --upgrade
fi

# Upgrade pip
echo "📦 Upgrading pip..."
python3 -m pip install --upgrade pip

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies from requirements.txt..."
    pip3 install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "⚠️  requirements.txt not found"
fi

# Check git
if command -v git &> /dev/null; then
    echo "✅ Git found: $(git --version)"
else
    echo "⚠️  Git not found (usually comes with Xcode tools)"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. If Xcode tools were missing, install them first"
echo "  2. Run this script again: bash setup.sh"
echo "  3. Start coding!"
