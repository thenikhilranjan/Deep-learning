# Git Setup Guide

## Quick Setup

### Automated Setup (Recommended)

Run the interactive setup script:
```bash
bash setup_git.sh
```

This script will:
- Check if Git is installed
- Configure your Git user name and email (if not set)
- Set up useful Git defaults
- Initialize the repository
- Create an initial commit

### Manual Setup

#### 1. Configure Git (Required First Time)

Set your name and email:
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

#### 2. Set Useful Defaults (Optional)

```bash
# Set default branch name to main
git config --global init.defaultBranch main

# Enable colored output
git config --global color.ui auto

# Set default editor (optional)
git config --global core.editor "nano"  # or "vim", "code", etc.
```

#### 3. Initialize Repository

```bash
git init
```

#### 4. Add Files and Create First Commit

```bash
git add .
git commit -m "Initial commit: Setup development environment"
```

## Verify Git Configuration

Check your Git settings:
```bash
git config --global --list
```

Check repository status:
```bash
git status
```

## Common Git Commands

```bash
# Check status
git status

# Add files
git add <file>          # Add specific file
git add .               # Add all files

# Commit changes
git commit -m "Your message"

# View commit history
git log

# Create a new branch
git branch <branch-name>
git checkout <branch-name>
# or in one command:
git checkout -b <branch-name>

# Switch branches
git checkout <branch-name>

# View differences
git diff
```

## Connecting to Remote Repository (GitHub, etc.)

### 1. Create a repository on GitHub (or your Git host)

### 2. Add remote and push

```bash
# Add remote repository
git remote add origin https://github.com/username/repository-name.git

# Push to remote
git push -u origin main
```

## Current Git Status

- ✅ Git is installed (version 2.50.1)
- ⚠️  Git global configuration needs to be set (user.name and user.email)
- ⚠️  Repository needs to be initialized

Run `bash setup_git.sh` to complete the setup!
