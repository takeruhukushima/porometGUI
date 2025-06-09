#!/bin/bash

echo "🚀 Poromet クイックスタート"
echo "=========================="

# Check if Python is available
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "❌ Python が見つかりません。Python 3.8+ をインストールしてください。"
        echo "   https://www.python.org/downloads/"
        exit 1
    fi
fi

echo "✅ Python: $($PYTHON_CMD --version)"

# Install dependencies automatically
echo "📦 必要な依存関係を自動インストール中..."
$PYTHON_CMD -m pip install --upgrade pip
$PYTHON_CMD -m pip install fastapi uvicorn python-multipart porespy numpy matplotlib scikit-image pillow

echo ""
echo "🔥 バックエンドサーバーを起動中..."
echo "   サーバーURL: http://127.0.0.1:8000"
echo "   停止するには Ctrl+C を押してください"
echo ""

# Navigate to backend directory and start server
if [ -f "backend/server.py" ]; then
    cd backend
    $PYTHON_CMD server.py
else
    echo "❌ backend/server.py が見つかりません"
    echo "   正しいディレクトリから実行していることを確認してください"
    exit 1
fi
