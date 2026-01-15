#!/bin/bash

# Git Setup Script
# This script helps configure git and initialize the repository

echo "🔧 Setting up Git..."
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed"
    echo "   Please install Xcode Command Line Tools: xcode-select --install"
    exit 1
fi

echo "✅ Git found: $(git --version)"
echo ""

# Check if git config is set
if [ -z "$(git config --global user.name)" ]; then
    echo "⚠️  Git user name is not configured"
    echo ""
    read -p "Enter your Git user name: " git_name
    if [ -n "$git_name" ]; then
        git config --global user.name "$git_name"
        echo "✅ Git user name set to: $git_name"
    else
        echo "⚠️  Skipping user name configuration"
    fi
else
    echo "✅ Git user name: $(git config --global user.name)"
fi

if [ -z "$(git config --global user.email)" ]; then
    echo "⚠️  Git user email is not configured"
    echo ""
    read -p "Enter your Git email: " git_email
    if [ -n "$git_email" ]; then
        git config --global user.email "$git_email"
        echo "✅ Git user email set to: $git_email"
    else
        echo "⚠️  Skipping email configuration"
    fi
else
    echo "✅ Git user email: $(git config --global user.email)"
fi

# Set some useful defaults
echo ""
echo "📝 Setting up Git defaults..."

# Set default branch name to main
git config --global init.defaultBranch main

# Set editor (use nano as default, user can change later)
if [ -z "$(git config --global core.editor)" ]; then
    git config --global core.editor "nano"
fi

# Enable colored output
git config --global color.ui auto

# Set pull strategy
git config --global pull.rebase false

# Set push default
git config --global push.default simple

echo "✅ Git defaults configured"
echo ""

# Initialize repository if not already initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing Git repository..."
    git init
    echo "✅ Git repository initialized"
    
    # Add all files
    echo ""
    echo "📝 Adding files to Git..."
    git add .
    
    # Create initial commit
    echo ""
    echo "💾 Creating initial commit..."
    git commit -m "Initial commit: Setup development environment"
    
    echo ""
    echo "✅ Git repository initialized and first commit created"
else
    echo "ℹ️  Git repository already initialized"
    echo ""
    echo "Current status:"
    git status --short
fi

echo ""
echo "✨ Git setup complete!"
echo ""
echo "Current Git configuration:"
echo "  User: $(git config --global user.name)"
echo "  Email: $(git config --global user.email)"
echo "  Default branch: $(git config --global init.defaultBranch)"
echo ""
echo "To view all Git config: git config --global --list"
