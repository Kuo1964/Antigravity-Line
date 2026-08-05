#!/bin/bash

# 專案絕對路徑
PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"

# 等待 Google Drive 雲端硬碟掛載完成（最多等待 60 秒）
MAX_RETRY=30
RETRY_COUNT=0

echo "⏳ 正在檢查 Google Drive 雲端硬碟掛載狀態..."
until [ -d "$PROJECT_DIR" ]; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRY ]; then
        echo "❌ 錯誤：超過 60 秒仍無法存取 Google Drive 專案目錄 ($PROJECT_DIR)"
        exit 1
    fi
    echo "⏳ 專案目錄尚未掛載，等待中... ($RETRY_COUNT/$MAX_RETRY)"
    sleep 2
done

cd "$PROJECT_DIR" || exit 1

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

echo "✅ 服務已成功啟動！(Press Ctrl+C to stop)"

# 捕捉 Ctrl+C 信號並清理進程
trap "kill $UVICORN_PID $NGROK_PID; exit" INT

wait
