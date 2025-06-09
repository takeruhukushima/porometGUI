#!/bin/bash

echo "🚀 Poromet 完全起動スクリプト"
echo "============================"

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 サーバーを停止中..."
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null
        echo "   バックエンドサーバーを停止しました"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null
        echo "   フロントエンドサーバーを停止しました"
    fi
    exit 0
}

trap cleanup INT TERM

# Check dependencies
echo "📦 依存関係を確認中..."

# Check Python
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        echo "❌ Python が見つかりません"
        exit 1
    fi
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js が見つかりません"
    exit 1
fi

# Check Python packages
$PYTHON_CMD -c "import porespy, fastapi, uvicorn" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Python 依存関係が不足しています"
    echo "   bash scripts/install-dependencies.sh を実行してください"
    exit 1
fi

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Node.js 依存関係をインストール中..."
    npm install
fi

echo "✅ すべての依存関係が利用可能です"
echo ""

# Start backend
echo "🔥 バックエンドサーバーを起動中..."
cd backend
$PYTHON_CMD server.py &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "⏳ バックエンドサーバーの起動を待機中..."
sleep 5

# Check if backend is running
curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ バックエンドサーバーが起動しました: http://127.0.0.1:8000"
else
    echo "❌ バックエンドサーバーの起動に失敗しました"
    cleanup
    exit 1
fi

# Start frontend
echo "🌐 フロントエンドサーバーを起動中..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "🎉 Poromet が正常に起動しました！"
echo "================================"
echo "   フロントエンド: http://localhost:3000"
echo "   バックエンド: http://127.0.0.1:8000"
echo "   API ドキュメント: http://127.0.0.1:8000/docs"
echo ""
echo "   両方のサーバーを停止するには Ctrl+C を押してください"
echo ""

# Wait for user to stop
wait
