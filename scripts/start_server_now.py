#!/usr/bin/env python3
"""
Immediate server starter - tries to start the server right now
"""

import sys
import os
import subprocess
import time

def find_server_file():
    """server.pyファイルを探す"""
    possible_paths = [
        "backend/server.py",
        "server.py", 
        "../backend/server.py",
        "./backend/server.py"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None

def start_server_direct():
    """サーバーを直接起動"""
    print("🚀 Poromet サーバー直接起動")
    print("=" * 30)
    
    # Find server file
    server_path = find_server_file()
    if not server_path:
        print("❌ server.py が見つかりません")
        return False
    
    print(f"📁 サーバーファイル: {server_path}")
    
    # Change directory if needed
    if server_path.startswith("backend/"):
        print("📂 backend ディレクトリに移動")
        os.chdir("backend")
        server_path = "server.py"
    elif server_path.startswith("../"):
        print("📂 親ディレクトリに移動")
        os.chdir("..")
        if os.path.exists("backend/server.py"):
            os.chdir("backend")
            server_path = "server.py"
    
    print("🔥 サーバー起動中...")
    print("URL: http://127.0.0.1:8000")
    print("Ctrl+C で停止")
    print("-" * 30)
    
    try:
        # Try to run the server
        subprocess.run([sys.executable, server_path])
        return True
    except KeyboardInterrupt:
        print("\n🛑 サーバーを停止しました")
        return True
    except FileNotFoundError:
        print("❌ Python が見つかりません")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False

if __name__ == "__main__":
    start_server_direct()
