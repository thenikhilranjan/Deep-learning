# Push to GitHub - Quick Guide

## ✅ Remote Configured

Your repository is connected to:
- **GitHub Username:** `thenikhilranjan`
- **Repository:** `cursior`
- **Remote URL:** `https://github.com/thenikhilranjan/cursior.git`

## 🚀 Push Your Code

### Step 1: Create the Repository on GitHub

**Important:** You need to create the repository on GitHub first!

1. Go to: https://github.com/new
2. Repository name: `cursior` (or change it if you want)
3. Choose **Public** or **Private**
4. **DO NOT** check "Initialize with README" (we already have files)
5. Click **"Create repository"**

### Step 2: Push Your Code

Once the repository exists on GitHub, run:

```bash
git push -u origin main
```

### Step 3: Authentication

When prompted:
- **Username:** `thenikhilranjan`
- **Password:** Use a **Personal Access Token** (not your GitHub password)

#### How to Create a Personal Access Token:

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Give it a name (e.g., "My Computer")
4. Select scope: **`repo`** (full control of private repositories)
5. Click **"Generate token"**
6. **Copy the token immediately** (you won't see it again!)
7. Use this token as your password when pushing

## ✅ Verify Connection

After pushing, verify it worked:

```bash
git remote -v
```

Your repository will be available at:
**https://github.com/thenikhilranjan/cursior**

## 🔄 Future Pushes

After the first push, you can simply use:

```bash
git push
```

## 📝 Change Repository Name?

If you want to use a different repository name, update the remote:

```bash
git remote set-url origin https://github.com/thenikhilranjan/YOUR_NEW_REPO_NAME.git
```

## 🆘 Troubleshooting

### "Repository not found"
- Make sure you created the repository on GitHub first
- Check the repository name matches

### "Authentication failed"
- Use a Personal Access Token, not your GitHub password
- Make sure the token has `repo` scope

### "Permission denied"
- Verify your username is correct: `thenikhilranjan`
- Check you have access to the repository
