#!/bin/bash

echo "🔍 Poromet システム状態チェック"
echo "=============================="

# Check Python
echo "Python:"
if command -v python &> /dev/null; then
    echo "  ✅ python: $(python --version)"
elif command -v python3 &> /dev/null; then
    echo "  ✅ python3: $(python3 --version)"
else
    echo "  ❌ Python が見つかりません"
fi

# Check Node.js
echo ""
echo "Node.js:"
if command -v node &> /dev/null; then
    echo "  ✅ node: $(node --version)"
else
    echo "  ❌ Node.js が見つかりません"
fi

if command -v npm &> /dev/null; then
    echo "  ✅ npm: $(npm --version)"
else
    echo "  ❌ npm が見つかりません"
fi

# Check Python packages
echo ""
echo "Python パッケージ:"
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

PACKAGES=("porespy" "fastapi" "uvicorn" "numpy" "matplotlib" "skimage" "PIL")
for package in "${PACKAGES[@]}"; do
    $PYTHON_CMD -c "import $package" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "  ✅ $package"
    else
        echo "  ❌ $package"
    fi
done

# Check servers
echo ""
echo "サーバー状態:"

# Check backend
curl -s http://127.0.0.1:8000/api/health > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ バックエンド: http://127.0.0.1:8000 (実行中)"
else
    echo "  ❌ バックエンド: http://127.0.0.1:8000 (停止中)"
fi

# Check frontend
curl -s http://localhost:3000 > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ フロントエンド: http://localhost:3000 (実行中)"
else
    echo "  ❌ フロントエンド: http://localhost:3000 (停止中)"
fi

echo ""
echo "📋 推奨アクション:"
echo "  1. 依存関係インストール: bash scripts/install-dependencies.sh"
echo "  2. バックエンド起動: bash scripts/start-backend.sh"
echo "  3. フロントエンド起動: bash scripts/start-frontend.sh"
echo "  4. 全て同時起動: bash scripts/start-all.sh"
