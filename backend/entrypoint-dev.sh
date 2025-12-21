#!/bin/bash
set -e

# プロジェクトのルートに移動
cd /app

# 1. 依存関係の同期
# コンテナ起動時にホスト側の pyproject.toml に合わせてライブラリをインストール
# app-python-packages ボリュームに .venv があるので、差分のみ高速に処理されます
echo "Running uv sync..."
uv sync --all-extras

# 2. サーバーの起動
# exec を使用して、現在のシェルプロセスを uvicorn プロセスに置き換える
# これにより、Ctrl+C や docker stop が即座に効くようになる
echo "Starting Uvicorn..."
exec uv run uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload