#!/bin/bash

echo "🌐 Poromet フロントエンド起動"
echo "============================"

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Node.js が見つかりません。Node.js 16+ をインストールしてください。"
    echo "   https://nodejs.org/"
    exit 1
fi

echo "✅ Node.js: $(node --version)"

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ npm が見つかりません。"
    exit 1
fi

echo "✅ npm: $(npm --version)"

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Node.js 依存関係をインストール中..."
    npm install
fi

echo ""
echo "🔥 フロントエンドサーバーを起動中..."
echo "   フロントエンドURL: http://localhost:3000"
echo ""
echo "   停止するには Ctrl+C を押してください"
echo ""

npm run dev
