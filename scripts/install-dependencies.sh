#!/bin/bash

echo "🔧 Poromet 依存関係インストール"
echo "================================"

# Check if Python is available
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "❌ Python が見つかりません。Python 3.8+ をインストールしてください。"
    echo "   https://www.python.org/downloads/"
    exit 1
fi

# Use python3 if python is not available
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

echo "✅ Python が見つかりました: $($PYTHON_CMD --version)"

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip が見つかりません。pip をインストールしてください。"
    exit 1
fi

PIP_CMD="pip"
if ! command -v pip &> /dev/null; then
    PIP_CMD="pip3"
fi

echo "✅ pip が見つかりました"

# Install required packages
echo ""
echo "📦 必要なPythonライブラリをインストール中..."
echo "   これには数分かかる場合があります..."

$PIP_CMD install fastapi uvicorn python-multipart porespy numpy matplotlib scikit-image pillow

if [ $? -eq 0 ]; then
    echo "✅ すべての依存関係のインストールが完了しました！"
    echo ""
    echo "🚀 次のステップ:"
    echo "   1. バックエンドサーバーを起動: bash scripts/start-backend.sh"
    echo "   2. フロントエンドを起動: npm run dev"
else
    echo "❌ 依存関係のインストールに失敗しました"
    echo "   手動でインストールしてください:"
    echo "   $PIP_CMD install fastapi uvicorn python-multipart porespy numpy matplotlib scikit-image pillow"
fi
