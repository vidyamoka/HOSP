#!/usr/bin/env python3
"""
Installation script for Python 3.14.2 compatibility
"""
import subprocess
import sys
import platform

def install_for_python_314():
    """Install packages compatible with Python 3.14"""
    print("Installing packages for Python 3.14.2...")
    
    # Try to get the latest compatible versions
    packages = [
        "setuptools>=68.0.0",
        "wheel>=0.41.0",
        "pip>=23.0.0"
    ]
    
    # Install build tools first
    for package in packages:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", package])
    
    # Main packages - let pip find compatible versions
    main_packages = [
        "Flask",
        "Flask-SQLAlchemy",
        "Werkzeug",
        "Pillow",
        "matplotlib",
        "numpy",
        "Jinja2",
        "python-dotenv"
    ]
    
    for package in main_packages:
        try:
            print(f"\nInstalling {package}...")
            # Try without version first
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError:
            print(f"Could not install {package}, trying from source...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--no-binary", package])

if __name__ == "__main__":
    install_for_python_314()