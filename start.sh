#!/bin/bash
set -e

# 環境変数の確認
echo "=== 環境変数 ==="
echo "PORT: $PORT"
echo "PYTHONPATH: $PYTHONPATH"

# 依存関係のインストール
pip install --no-cache-dir -r requirements.txt

# バックエンドとフロントエンドを並行して起動
echo "=== アプリケーションを起動します ==="

# バックエンドをバックグラウンドで起動
uvicorn backend.server:app --host 0.0.0.0 --port $PORT --log-level debug &

# フロントエンドのビルドと起動
cd /app
npm run build
npm run start -- -p 3000 &

# 両方のプロセスが終了するのを待機
wait
