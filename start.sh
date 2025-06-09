#!/bin/bash
set -e

# 環境変数の確認
echo "=== 環境変数 ==="
echo "PORT: $PORT"
echo "PYTHONPATH: $PYTHONPATH"

# 依存関係のインストール
pip install --no-cache-dir -r requirements.txt

# アプリケーションの起動
echo "=== アプリケーションを起動します ==="
uvicorn backend.server:app --host 0.0.0.0 --port $PORT --log-level debug
