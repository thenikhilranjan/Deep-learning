#!/bin/bash

# GitHub Connection Script
# This script helps connect your local repository to GitHub

echo "🔗 GitHub Connection Setup"
echo "=========================="
echo ""

# Check if git is configured
if [ -z "$(git config --global user.name)" ] || [ -z "$(git config --global user.email)" ]; then
    echo "⚠️  Git identity not configured. Setting up first..."
    echo ""
    read -p "Enter your Git user name: " git_name
    read -p "Enter your Git email: " git_email
    
    if [ -n "$git_name" ] && [ -n "$git_email" ]; then
        git config --global user.name "$git_name"
        git config --global user.email "$git_email"
        echo "✅ Git identity configured"
    else
        echo "❌ Git identity required. Exiting."
        exit 1
    fi
    echo ""
fi

# Check if remote already exists
if git remote get-url origin &> /dev/null; then
    echo "⚠️  Remote 'origin' already exists:"
    git remote -v
    echo ""
    read -p "Do you want to update it? (y/n): " update_remote
    if [ "$update_remote" != "y" ]; then
        echo "Exiting. No changes made."
        exit 0
    fi
fi

echo "📋 To connect to GitHub, you need:"
echo "   1. A GitHub account (https://github.com)"
echo "   2. A repository on GitHub (create one at https://github.com/new)"
echo ""

# Get repository URL
echo "Enter your GitHub repository URL:"
echo "   Examples:"
echo "   - HTTPS: https://github.com/username/repository-name.git"
echo "   - SSH:   git@github.com:username/repository-name.git"
echo ""
read -p "Repository URL: " repo_url

if [ -z "$repo_url" ]; then
    echo "❌ Repository URL is required. Exiting."
    exit 1
fi

# Add or update remote
echo ""
if git remote get-url origin &> /dev/null; then
    echo "🔄 Updating remote 'origin'..."
    git remote set-url origin "$repo_url"
else
    echo "➕ Adding remote 'origin'..."
    git remote add origin "$repo_url"
fi

# Verify remote
echo ""
echo "✅ Remote configured:"
git remote -v
echo ""

# Check if we should push
read -p "Do you want to push your code to GitHub now? (y/n): " push_now

if [ "$push_now" = "y" ]; then
    echo ""
    echo "📤 Pushing to GitHub..."
    
    # Check if branch is 'main' or 'master'
    current_branch=$(git branch --show-current)
    
    # Push to GitHub
    if git push -u origin "$current_branch"; then
        echo ""
        echo "✅ Successfully pushed to GitHub!"
        echo ""
        echo "🌐 Your repository is now available at:"
        # Extract repo URL without .git
        repo_web_url=$(echo "$repo_url" | sed 's/\.git$//' | sed 's/git@github.com:/https:\/\/github.com\//')
        echo "   $repo_web_url"
    else
        echo ""
        echo "❌ Push failed. Common issues:"
        echo "   1. Repository doesn't exist on GitHub - create it first"
        echo "   2. Authentication required - you may need to:"
        echo "      - Use a Personal Access Token (HTTPS)"
        echo "      - Set up SSH keys (SSH)"
        echo "      - Install GitHub CLI: brew install gh && gh auth login"
        echo ""
        echo "💡 Try pushing manually: git push -u origin $current_branch"
    fi
else
    echo ""
    echo "ℹ️  Remote configured. Push manually when ready:"
    current_branch=$(git branch --show-current)
    echo "   git push -u origin $current_branch"
fi

echo ""
echo "✨ Setup complete!"
