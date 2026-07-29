#!/bin/bash

# Antigravity LINE Bot 自動執行服務安裝腳本 (macOS Launchd)

PLIST_NAME="com.antigravity.linebot.plist"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TARGET_DIR="$HOME/Library/LaunchAgents"

echo "🚀 開始安裝 Antigravity LINE Bot 開機/登入自動執行服務..."

# 建立 LaunchAgents 資料夾 (若不存在)
mkdir -p "$TARGET_DIR"

# 複製 plist 檔案
cp "$SCRIPT_DIR/$PLIST_NAME" "$TARGET_DIR/$PLIST_NAME"

# 若服務正運行中則先解除載入
launchctl unload "$TARGET_DIR/$PLIST_NAME" 2>/dev/null || true

# 載入並啟動服務
launchctl load -w "$TARGET_DIR/$PLIST_NAME"

echo "✅ 成功安裝並啟用開機自動執行服務！"
echo "📍 服務狀態: 已由 macOS launchd 託管 (Port 8000)"
echo "📄 日誌紀錄檔: app.log 與 app.err"
