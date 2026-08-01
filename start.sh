#!/bin/bash

# 啟用 Python 虛擬環境
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "🚀 正在啟動 FastAPI Webhook 服務 (Port 8000)..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app &
UVICORN_PID=$!

echo "🔗 正在啟動 ngrok 外網轉接 (Port 8000)..."
ngrok http 8000 &
NGROK_PID=$!

echo "✅ 服務已於背景成功啟動！(Press Ctrl+C to stop all)"

# 捕捉 Ctrl+C 信號並清理進程
trap "kill $UVICORN_PID $NGROK_PID; exit" INT

wait
