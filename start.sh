#!/bin/bash
# ==============================================================================
# Antigravity Line Bot Bridge - 完全解耦系統層級 Daemon 守護進程啟動腳本
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "🧹 清理舊有服務進程..."
pkill -9 -f "uvicorn app.main:app" >/dev/null 2>&1 || true
pkill -9 -f "ngrok http" >/dev/null 2>&1 || true
sleep 1

echo "🟢 正在以完全獨立 Daemon 啟動 FastAPI (Uvicorn) 伺服器 (Port 8000)..."
(nohup ./venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 > uvicorn.log 2>&1 &)
sleep 2

echo "🌐 正在以完全獨立 Daemon 啟動 ngrok 外網隧道..."
(nohup ngrok http 127.0.0.1:8000 > ngrok.log 2>&1 &)
sleep 3

# 驗證進程
UVICORN_PID=$(pgrep -f "uvicorn app.main:app" | head -n 1 || echo "")
NGROK_PID=$(pgrep -f "ngrok http" | head -n 1 || echo "")

echo "🎉 服務一鍵 Daemon 常駐啟動完畢！"
echo "──────────────────────────────────────────"
echo "FastAPI PID : ${UVICORN_PID:-未偵測到}"
echo "ngrok PID   : ${NGROK_PID:-未偵測到}"
echo "FastAPI 健康檢查: http://127.0.0.1:8000/health"
echo "ngrok 管理面板  : http://127.0.0.1:4040"
echo "──────────────────────────────────────────"

NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o '"public_url":"[^"]*' | head -n 1 | cut -d'"' -f4 || echo "")

if [ -n "$NGROK_URL" ]; then
    echo "🔗 目前 ngrok Webhook 網址為:"
    echo "   ${NGROK_URL}/webhook"
    echo ""
    echo "💡 請確保 LINE Developers 後台的 Webhook URL 已設定為此網址！"
fi
