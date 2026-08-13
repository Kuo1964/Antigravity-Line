#!/bin/bash
# Antigravity Line Bot 一鍵啟動腳本 (FastAPI + ngrok)

PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
cd "$PROJECT_DIR" || exit 1

echo "🚀 [1/3] 正在載入 Python 虛擬環境..."
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

echo "🟢 [2/3] 正在背景啟動 FastAPI (Uvicorn) 伺服器 (Port 8000)..."
nohup python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &
UVICORN_PID=$!
echo "   └─ FastAPI 服務已啟動 (PID: $UVICORN_PID)"

sleep 2

echo "🌐 [3/3] 正在背景啟動 ngrok 外網穿透隧道 (Port 8000)..."
nohup ngrok http 8000 > /dev/null 2>&1 &
NGROK_PID=$!
echo "   └─ ngrok 服務已啟動 (PID: $NGROK_PID)"

sleep 3

echo ""
echo "🎉 服務一鍵啟動完畢！"
echo "──────────────────────────────────────────"
echo "FastAPI 健康檢查: http://127.0.0.1:8000/health"
echo "ngrok 管理面板  : http://127.0.0.1:4040"
echo "──────────────────────────────────────────"

# 取得 ngrok 公開 URL
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c "import sys, json; print(json.load(sys.stdin)['tunnels'][0]['public_url'])" 2>/dev/null)
if [ -n "$NGROK_URL" ]; then
    echo "🔗 目前 ngrok Webhook 網址為:"
    echo "   $NGROK_URL/webhook"
    echo ""
    echo "💡 請確保 LINE Developers 後台的 Webhook URL 已設定為此網址！"
fi
