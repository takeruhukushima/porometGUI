# Pythonの公式イメージをベースに使用
FROM python:3.12-slim

# 環境変数を設定
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

# 作業ディレクトリを設定
WORKDIR /app

# システムパッケージのインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションのコードをコピー
COPY . .

# ポートを公開
EXPOSE $PORT

# ヘルスチェック用のエンドポイントを追加
RUN echo 'from fastapi import FastAPI; app = FastAPI(); @app.get("/health") async def health_check(): return {"status": "ok"}' > /app/health_check.py

# アプリケーションを起動
CMD ["sh", "-c", "uvicorn backend.server:app --host 0.0.0.0 --port $PORT --reload"]
