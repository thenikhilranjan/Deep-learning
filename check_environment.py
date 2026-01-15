#!/usr/bin/env python3
"""
Environment Check Script
Checks if all basic development tools are installed and configured.
"""

import sys
import subprocess
import shutil

def check_command(cmd, name):
    """Check if a command exists and is accessible."""
    if shutil.which(cmd):
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"✅ {name}: {version}")
                return True
            else:
                print(f"⚠️  {name}: Found but version check failed")
                return False
        except Exception as e:
            print(f"⚠️  {name}: Found but error checking version: {e}")
            return False
    else:
        print(f"❌ {name}: Not found")
        return False

def check_python_packages():
    """Check if essential Python packages are installed."""
    essential_packages = {
        'pytest': 'pytest',
        'black': 'black',
        'flake8': 'flake8',
    }
    
    print("\n📦 Checking Python packages:")
    all_installed = True
    
    for package_name, import_name in essential_packages.items():
        try:
            __import__(import_name)
            print(f"✅ {package_name}: Installed")
        except ImportError:
            print(f"❌ {package_name}: Not installed")
            all_installed = False
    
    return all_installed

def check_git_config():
    """Check Git configuration and repository status."""
    print("\n🔧 Checking Git configuration:")
    git_configured = True
    
    # Check user name
    try:
        result = subprocess.run(['git', 'config', '--global', 'user.name'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Git user name: {result.stdout.strip()}")
        else:
            print("⚠️  Git user name: Not configured")
            git_configured = False
    except Exception:
        print("⚠️  Git user name: Not configured")
        git_configured = False
    
    # Check user email
    try:
        result = subprocess.run(['git', 'config', '--global', 'user.email'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            print(f"✅ Git user email: {result.stdout.strip()}")
        else:
            print("⚠️  Git user email: Not configured")
            git_configured = False
    except Exception:
        print("⚠️  Git user email: Not configured")
        git_configured = False
    
    # Check if repository is initialized
    try:
        result = subprocess.run(['git', 'rev-parse', '--git-dir'],
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Git repository: Initialized")
        else:
            print("⚠️  Git repository: Not initialized")
    except Exception:
        print("⚠️  Git repository: Not initialized")
    
    return git_configured

def main():
    print("🔍 Development Environment Check\n")
    print("=" * 50)
    
    # Check Python version
    print(f"\n🐍 Python Version: {sys.version}")
    print(f"   Python Path: {sys.executable}")
    
    # Check essential commands
    print("\n🛠️  Checking development tools:")
    tools = {
        'python3': 'Python 3',
        'pip3': 'pip3',
        'git': 'Git',
    }
    
    all_tools_ok = True
    for cmd, name in tools.items():
        if not check_command(cmd, name):
            all_tools_ok = False
    
    # Check Python packages
    packages_ok = check_python_packages()
    
    # Check Git configuration
    git_configured = check_git_config()
    
    # Summary
    print("\n" + "=" * 50)
    print("\n📊 Summary:")
    
    all_ok = all_tools_ok and packages_ok and git_configured
    
    if all_ok:
        print("✅ All checks passed! Your environment is ready.")
        return 0
    else:
        print("⚠️  Some checks failed. Please review the output above.")
        if not all_tools_ok:
            print("\n💡 To fix missing tools:")
            print("   1. Install Xcode Command Line Tools: xcode-select --install")
            print("   2. Install Python packages: pip3 install -r requirements.txt")
        if not git_configured:
            print("\n💡 To configure Git:")
            print("   Run: bash setup_git.sh")
            print("   Or manually: git config --global user.name 'Your Name'")
            print("                git config --global user.email 'your.email@example.com'")
        return 1

if __name__ == '__main__':
    sys.exit(main())
