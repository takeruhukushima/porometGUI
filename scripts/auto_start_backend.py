#!/usr/bin/env python3
"""
Poromet Backend Auto Starter
システムをチェックし、依存関係をインストールしてサーバーを起動
"""

import subprocess
import sys
import os
import time
import platform

def run_command(command, description=""):
    """コマンドを実行し、結果を返す"""
    try:
        print(f"🔄 {description}...")
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            return True, result.stdout
        else:
            print(f"❌ {description} 失敗: {result.stderr}")
            return False, result.stderr
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} タイムアウト")
        return False, "Timeout"
    except Exception as e:
        print(f"❌ {description} エラー: {e}")
        return False, str(e)

def check_python():
    """Python環境をチェック"""
    print("🐍 Python環境をチェック中...")
    
    # Python version check
    version = sys.version_info
    print(f"Python バージョン: {version.major}.{version.minor}.{version.micro}")
    
    if version < (3, 8):
        print("❌ Python 3.8以上が必要です")
        return False
    
    print("✅ Python バージョンOK")
    return True

def install_package(package_name):
    """パッケージをインストール"""
    commands = [
        f"{sys.executable} -m pip install {package_name}",
        f"{sys.executable} -m pip install --user {package_name}",
        f"pip install {package_name}",
        f"pip3 install {package_name}"
    ]
    
    for cmd in commands:
        success, output = run_command(cmd, f"Installing {package_name}")
        if success:
            return True
    
    return False

def check_and_install_dependencies():
    """依存関係をチェックしてインストール"""
    print("\n📦 依存関係をチェック中...")
    
    packages = {
        'fastapi': 'fastapi',
        'uvicorn': 'uvicorn[standard]',
        'multipart': 'python-multipart',
        'numpy': 'numpy',
        'matplotlib': 'matplotlib',
        'skimage': 'scikit-image',
        'PIL': 'pillow',
        'porespy': 'porespy'
    }
    
    missing_packages = []
    
    for import_name, package_name in packages.items():
        try:
            if import_name == 'multipart':
                import multipart
            elif import_name == 'skimage':
                import skimage
            elif import_name == 'PIL':
                import PIL
            else:
                __import__(import_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} (インストールが必要)")
            missing_packages.append(package_name)
    
    if missing_packages:
        print(f"\n📥 {len(missing_packages)}個のパッケージをインストール中...")
        
        # Try to upgrade pip first
        run_command(f"{sys.executable} -m pip install --upgrade pip", "pip upgrade")
        
        # Install missing packages
        for package in missing_packages:
            print(f"\n📦 {package} をインストール中...")
            if not install_package(package):
                print(f"❌ {package} のインストールに失敗しました")
                return False
        
        print("\n✅ すべての依存関係がインストールされました！")
    else:
        print("\n✅ すべての依存関係が利用可能です！")
    
    return True

def start_server():
    """サーバーを起動"""
    print("\n🚀 Porometバックエンドサーバーを起動中...")
    
    # Check if server.py exists
    server_paths = [
        "backend/server.py",
        "server.py",
        "../backend/server.py"
    ]
    
    server_path = None
    for path in server_paths:
        if os.path.exists(path):
            server_path = path
            break
    
    if not server_path:
        print("❌ server.py が見つかりません")
        print("以下の場所を確認してください:")
        for path in server_paths:
            print(f"  - {path}")
        return False
    
    print(f"📁 サーバーファイル: {server_path}")
    
    # Change to the correct directory
    if server_path.startswith("backend/"):
        os.chdir("backend")
        server_path = "server.py"
    elif server_path.startswith("../"):
        os.chdir("../backend")
        server_path = "server.py"
    
    print("🔥 サーバー起動中...")
    print("=" * 50)
    print("サーバーURL: http://127.0.0.1:8000")
    print("ヘルスチェック: http://127.0.0.1:8000/api/health")
    print("API ドキュメント: http://127.0.0.1:8000/docs")
    print("停止するには Ctrl+C を押してください")
    print("=" * 50)
    
    try:
        # Import and run the server
        import importlib.util
        spec = importlib.util.spec_from_file_location("server", server_path)
        server_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server_module)
        
    except KeyboardInterrupt:
        print("\n\n🛑 サーバーが停止されました")
        return True
    except Exception as e:
        print(f"\n❌ サーバー起動エラー: {e}")
        return False

def main():
    """メイン処理"""
    print("🚀 Poromet Backend Auto Starter")
    print("=" * 50)
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"アーキテクチャ: {platform.machine()}")
    
    # Step 1: Check Python
    if not check_python():
        print("\n❌ Python環境に問題があります")
        return False
    
    # Step 2: Install dependencies
    if not check_and_install_dependencies():
        print("\n❌ 依存関係のインストールに失敗しました")
        return False
    
    # Step 3: Start server
    if not start_server():
        print("\n❌ サーバーの起動に失敗しました")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n🔧 手動でのインストールを試してください:")
            print("pip install fastapi uvicorn python-multipart porespy numpy matplotlib scikit-image pillow")
            print("python backend/server.py")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 終了しました")
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        sys.exit(1)
