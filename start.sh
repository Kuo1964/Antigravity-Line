#!/bin/bash
# ==============================================================================
# Antigravity Line Bot Bridge - 終極 < /dev/null 完全脫離 stdin 守護啟動腳本
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

PYTHON_BIN="$PROJECT_DIR/venv/bin/python"
NGROK_BIN="/opt/homebrew/bin/ngrok"

if [ ! -f "$NGROK_BIN" ]; then
    NGROK_BIN="$(which ngrok || echo "ngrok")"
fi

echo "🧹 清理舊有殘留進程..."
pkill -9 -f "uvicorn app.main:app" >/dev/null 2>&1 || true
pkill -9 -f "ngrok http" >/dev/null 2>&1 || true
sleep 1

echo "🟢 [1/2] 啟動 FastAPI 服務 (Port 8000)..."
(nohup "$PYTHON_BIN" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 < /dev/null > uvicorn.log 2>&1 &)
sleep 2

echo "🌐 [2/2] 啟動 ngrok (Port 8000) 完全解耦守護進程..."
(nohup "$NGROK_BIN" http 8000 --log=stdout < /dev/null > ngrok.log 2>&1 &)
sleep 4

NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o '"public_url":"[^"]*' | head -n 1 | cut -d'"' -f4 || echo "")

echo "🎉 服務已徹底脫離 Shell 生命週期常駐啟動完畢！"
echo "──────────────────────────────────────────"
echo "FastAPI PID : $(pgrep -f "uvicorn app.main:app" | head -n 1)"
echo "ngrok PID   : $(pgrep -f "ngrok http" | head -n 1)"
echo "FastAPI 健康檢查: http://127.0.0.1:8000/health"
echo "ngrok 管理面板  : http://127.0.0.1:4040"
echo "──────────────────────────────────────────"

if [ -n "$NGROK_URL" ]; then
    echo "🔗 目前活著的對外 ngrok Webhook 網址為:"
    echo "   ${NGROK_URL}/webhook"
fi
