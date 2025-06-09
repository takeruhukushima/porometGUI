#!/usr/bin/env python3
"""
Poromet Backend Server Starter
自動的に依存関係をインストールしてサーバーを起動します
"""

import subprocess
import sys
import os
import importlib.util

def check_and_install_package(package_name, import_name=None):
    """パッケージがインストールされているかチェックし、なければインストール"""
    if import_name is None:
        import_name = package_name
    
    try:
        if import_name == "skimage":
            import skimage
        elif import_name == "PIL":
            import PIL
        elif import_name == "multipart":
            import multipart
        else:
            __import__(import_name)
        print(f"✅ {package_name} is available")
        return True
    except ImportError:
        print(f"❌ {package_name} not found. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"✅ {package_name} installed successfully")
            return True
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package_name}")
            return False

def main():
    print("🚀 Poromet Backend Server Starter")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version}")
    
    # Required packages
    packages = [
        ("fastapi", "fastapi"),
        ("uvicorn[standard]", "uvicorn"),
        ("python-multipart", "multipart"),
        ("numpy", "numpy"),
        ("matplotlib", "matplotlib"),
        ("scikit-image", "skimage"),
        ("pillow", "PIL"),
        ("porespy", "porespy")
    ]
    
    print("\n📦 Checking dependencies...")
    
    all_installed = True
    for package, import_name in packages:
        if not check_and_install_package(package, import_name):
            all_installed = False
    
    if not all_installed:
        print("\n❌ Some packages failed to install")
        print("Try manual installation:")
        print("pip install fastapi uvicorn python-multipart numpy matplotlib scikit-image pillow porespy")
        sys.exit(1)
    
    print("\n✅ All dependencies are available!")
    
    # Start the server
    print("\n🔥 Starting Poromet Backend Server...")
    print("Server URL: http://127.0.0.1:8000")
    print("Health check: http://127.0.0.1:8000/api/health")
    print("API docs: http://127.0.0.1:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    # Import and run the server
    try:
        # Change to backend directory if it exists
        if os.path.exists("backend") and os.path.isfile("backend/server.py"):
            os.chdir("backend")
            
        # Import the server module
        if os.path.isfile("server.py"):
            import server
        else:
            print("❌ server.py not found")
            print("Make sure you're in the correct directory")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
