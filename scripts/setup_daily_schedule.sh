#!/usr/bin/env bash
# macOS 硬體喚醒與雙時區 LINE 早安圖 Crontab 一鍵自動化設定腳本 (V16)

PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"

echo "============================================================"
echo " 🚀 開始部署 Antigravity-Line 現代化排程系統 (V16) "
echo "============================================================"
echo "系統需要您的 Mac 管理員密碼來設定 Root 喚醒權限..."
sudo echo "✓ 密碼驗證成功"

cd "$PROJECT_DIR"
PYTHONPATH=. ./venv/bin/python scripts/deploy_schedule.py
