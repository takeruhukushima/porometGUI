#!/bin/bash

echo "🚀 Poromet 実際の細孔解析バックエンドを起動中..."
echo "================================================"

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "❌ Python が見つかりません。Python をインストールしてください。"
    exit 1
fi

# Check if we're in the backend directory
if [ ! -f "server.py" ]; then
    echo "📁 backend ディレクトリに移動中..."
    cd backend
fi

# Check if required packages are installed
echo "📦 Python 依存関係を確認中..."
python -c "import porespy, fastapi, uvicorn, numpy, matplotlib, skimage" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📥 Python 依存関係をインストール中..."
    echo "必要なパッケージ: porespy, fastapi, uvicorn, numpy, matplotlib, scikit-image, pillow"
    pip install fastapi uvicorn python-multipart porespy numpy matplotlib scikit-image pillow
fi

echo "✅ 依存関係の確認完了"
echo "🔥 実際の細孔解析バックエンドサーバーを起動中..."
echo "注意: 実際の解析には時間がかかります"

python server.py
