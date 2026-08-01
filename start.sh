#!/bin/bash

# 專案絕對路徑
PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
cd "$PROJECT_DIR"

# 啟用 Python 虛擬環境
if [ -d "$PROJECT_DIR/venv" ]; then
    source "$PROJECT_DIR/venv/bin/activate"
fi

export PATH="/opt/homebrew/bin:$PATH"

echo "🚀 正在啟動 FastAPI Webhook 服務 (Port 8000)..."
"$PROJECT_DIR/venv/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app &
UVICORN_PID=$!

echo "🔗 正在啟動 ngrok 外網轉接 (Port 8000)..."
/opt/homebrew/bin/ngrok http 8000 &
NGROK_PID=$!

echo "✅ 服務已於背景成功啟動！"

# 捕捉 Ctrl+C 信號並清理進程
trap "kill $UVICORN_PID $NGROK_PID; exit" INT

wait
