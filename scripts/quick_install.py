#!/usr/bin/env python3
"""
Quick dependency installer for Poromet
"""

import subprocess
import sys
import os

def install_dependencies():
    """必要な依存関係を一括インストール"""
    print("📦 Poromet 依存関係インストーラー")
    print("=" * 40)
    
    # Required packages
    packages = [
        "fastapi",
        "uvicorn[standard]", 
        "python-multipart",
        "numpy",
        "matplotlib",
        "scikit-image",
        "pillow",
        "porespy"
    ]
    
    print(f"インストール対象: {len(packages)}個のパッケージ")
    for pkg in packages:
        print(f"  - {pkg}")
    
    print("\n🔄 インストール開始...")
    
    # Upgrade pip first
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ pip をアップグレードしました")
    except:
        print("⚠️ pip のアップグレードに失敗しましたが、続行します")
    
    # Install packages
    failed_packages = []
    
    for package in packages:
        try:
            print(f"\n📥 {package} をインストール中...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", package
            ], timeout=300)  # 5 minute timeout per package
            print(f"✅ {package} インストール完了")
        except subprocess.TimeoutExpired:
            print(f"⏰ {package} インストールタイムアウト")
            failed_packages.append(package)
        except subprocess.CalledProcessError:
            print(f"❌ {package} インストール失敗")
            failed_packages.append(package)
    
    # Summary
    print("\n" + "=" * 40)
    if failed_packages:
        print(f"❌ {len(failed_packages)}個のパッケージでエラー:")
        for pkg in failed_packages:
            print(f"  - {pkg}")
        print("\n🔧 手動インストールを試してください:")
        for pkg in failed_packages:
            print(f"pip install {pkg}")
        return False
    else:
        print("✅ すべての依存関係のインストールが完了しました！")
        print("\n🚀 次のステップ:")
        print("python backend/server.py")
        return True

if __name__ == "__main__":
    install_dependencies()
