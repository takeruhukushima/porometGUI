# Node.jsの公式イメージをベースに使用
FROM node:20 AS frontend-builder

# フロントエンドのビルド
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

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

# バックエンドの依存関係をインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# バックエンドのコードをコピー
COPY . .

# フロントエンドのビルド済みファイルをコピー
COPY --from=frontend-builder /app/.next /app/.next
COPY --from=frontend-builder /app/public /app/public

# 起動スクリプトを実行可能に
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# ポートを公開
EXPOSE $PORT

# アプリケーションを起動
CMD ["/app/start.sh"]
