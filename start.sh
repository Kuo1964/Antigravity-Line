#!/bin/bash
# ==============================================================================
# Antigravity Line Bot Bridge - 系統常駐 Daemon 啟動腳本
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "🧹 清理舊有服務進程..."
pkill -9 -f "uvicorn app.main:app" >/dev/null 2>&1 || true
pkill -9 -f "ngrok http" >/dev/null 2>&1 || true
sleep 1

echo "🟢 啟動 FastAPI 伺服器 (Port 8000)..."
./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
UVICORN_PID=$!
sleep 2

echo "🌐 啟動 ngrok 外網隧道..."
ngrok http 127.0.0.1:8000 > ngrok.log 2>&1 &
NGROK_PID=$!
sleep 3

echo "🎉 服務常駐啟動完成！"
echo "──────────────────────────────────────────"
echo "FastAPI PID : $UVICORN_PID"
echo "ngrok PID   : $NGROK_PID"
echo "FastAPI 健康檢查: http://127.0.0.1:8000/health"
echo "ngrok 管理面板  : http://127.0.0.1:4040"
echo "──────────────────────────────────────────"

NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o '"public_url":"[^"]*' | head -n 1 | cut -d'"' -f4 || echo "")

if [ -n "$NGROK_URL" ]; then
    echo "🔗 LINE Developers 後台 Webhook URL 請設定為:"
    echo "   ${NGROK_URL}/webhook"
fi
