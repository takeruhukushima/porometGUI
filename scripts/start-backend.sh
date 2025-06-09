#!/bin/bash

echo "🚀 Poromet バックエンドサーバー起動"
echo "=================================="

# Check if Python is available
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "❌ Python が見つかりません。Python 3.8+ をインストールしてください。"
        exit 1
    fi
fi

echo "✅ Python: $($PYTHON_CMD --version)"

# Check if required packages are installed
echo "📦 依存関係を確認中..."
$PYTHON_CMD -c "
try:
    import porespy, fastapi, uvicorn, numpy, matplotlib, skimage, PIL
    print('✅ すべての必要なライブラリが利用可能です')
except ImportError as e:
    print(f'❌ 必要なライブラリが見つかりません: {e}')
    print('   次のコマンドでインストールしてください:')
    print('   bash scripts/install-dependencies.sh')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo ""
    echo "🔧 依存関係をインストールしますか? (y/n)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        bash scripts/install-dependencies.sh
    else
        echo "依存関係をインストールしてから再度実行してください。"
        exit 1
    fi
fi

# Navigate to backend directory
if [ ! -f "backend/server.py" ]; then
    echo "❌ backend/server.py が見つかりません"
    echo "   正しいディレクトリから実行していることを確認してください"
    exit 1
fi

echo ""
echo "🔥 バックエンドサーバーを起動中..."
echo "   サーバーURL: http://127.0.0.1:8000"
echo "   ヘルスチェック: http://127.0.0.1:8000/api/health"
echo "   API ドキュメント: http://127.0.0.1:8000/docs"
echo ""
echo "   停止するには Ctrl+C を押してください"
echo ""

cd backend
$PYTHON_CMD server.py
