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

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip in virtual environment
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo "📦 Installing Python dependencies from requirements.txt..."
    pip install -r requirements.txt
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
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run environment check: python3 check_environment.py"
echo "  3. Start coding!"
echo ""
echo "Note: Remember to activate the virtual environment before working:"
echo "      source venv/bin/activate"
