# GitHub Connection Guide

## Quick Setup

### Automated Setup (Recommended)

Run the interactive script:
```bash
bash connect_github.sh
```

This script will guide you through:
- Configuring Git identity (if needed)
- Adding your GitHub repository URL
- Pushing your code to GitHub

## Manual Setup

### Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and sign in
2. Click the **"+"** icon in the top right → **"New repository"**
3. Enter a repository name (e.g., `cursior` or `unit-testing-assignment`)
4. Choose **Public** or **Private**
5. **DO NOT** initialize with README, .gitignore, or license (we already have these)
6. Click **"Create repository"**

### Step 2: Connect Local Repository to GitHub

#### Option A: Using HTTPS (Easier, requires authentication)

```bash
# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Verify remote
git remote -v

# Push your code
git push -u origin main
```

**Authentication:** When pushing, GitHub will prompt for:
- Username: Your GitHub username
- Password: Use a **Personal Access Token** (not your GitHub password)

**To create a Personal Access Token:**
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Select scopes: `repo` (full control of private repositories)
4. Copy the token and use it as your password

#### Option B: Using SSH (More secure, requires SSH key setup)

```bash
# Add remote repository
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO_NAME.git

# Verify remote
git remote -v

# Push your code
git push -u origin main
```

**SSH Key Setup:**
1. Generate SSH key: `ssh-keygen -t ed25519 -C "your_email@example.com"`
2. Add to SSH agent: `eval "$(ssh-agent -s)"` then `ssh-add ~/.ssh/id_ed25519`
3. Copy public key: `cat ~/.ssh/id_ed25519.pub`
4. GitHub → Settings → SSH and GPG keys → New SSH key → Paste and save

### Step 3: Verify Connection

```bash
# Check remote
git remote -v

# View repository on GitHub
# Open: https://github.com/YOUR_USERNAME/YOUR_REPO_NAME
```

## Using GitHub CLI (Alternative Method)

If you have GitHub CLI installed:

```bash
# Install GitHub CLI (if not installed)
brew install gh

# Authenticate
gh auth login

# Create repository and push in one command
gh repo create YOUR_REPO_NAME --public --source=. --remote=origin --push
```

## Common Commands

```bash
# View remotes
git remote -v

# Change remote URL
git remote set-url origin NEW_URL

# Remove remote
git remote remove origin

# Push changes
git push

# Pull changes
git pull

# Fetch changes (without merging)
git fetch
```

## Troubleshooting

### "Repository not found"
- Make sure the repository exists on GitHub
- Check the repository URL is correct
- Verify you have access to the repository

### "Authentication failed"
- **HTTPS:** Use a Personal Access Token instead of password
- **SSH:** Make sure your SSH key is added to GitHub
- Try: `gh auth login` (if GitHub CLI is installed)

### "Permission denied"
- Check your GitHub username and repository name
- Verify you have write access to the repository
- For organizations, check repository permissions

### "Updates were rejected"
- Someone else pushed to the repository
- Pull first: `git pull origin main --rebase`
- Then push: `git push`

## Current Status

- ✅ Local Git repository initialized
- ✅ Commits ready to push
- ⚠️  GitHub remote needs to be configured

Run `bash connect_github.sh` to get started!
