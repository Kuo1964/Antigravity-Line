#!/bin/bash
# ==============================================================================
# Antigravity Line Bot Bridge - 防 zsh: killed 永久常駐背景腳本
# ==============================================================================

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "🧹 強制清理舊有進程..."
killall -9 python3 uvicorn ngrok >/dev/null 2>&1 || true
sleep 1

echo "🟢 啟動 FastAPI 服務 (Port 8000)..."
(nohup ./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &)

echo "🌐 啟動 ngrok 隧道..."
(nohup ngrok http 8000 --log=stdout > ngrok.log 2>&1 &)

sleep 3

echo "🎉 服務已成功脫離 zsh 監管並永久常駐背景！"
echo "──────────────────────────────────────────"
echo "FastAPI 健康檢查: http://127.0.0.1:8000/health"
echo "ngrok 管理面板  : http://127.0.0.1:4040"
echo "──────────────────────────────────────────"

NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | grep -o '"public_url":"[^"]*' | head -n 1 | cut -d'"' -f4 || echo "")

if [ -n "$NGROK_URL" ]; then
    echo "🔗 目前實體 ngrok Webhook 網址為:"
    echo "   ${NGROK_URL}/webhook"
fi
