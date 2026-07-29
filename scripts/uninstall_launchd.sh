#!/bin/bash

# Antigravity LINE Bot 自動執行服務卸載腳本

PLIST_NAME="com.antigravity.linebot.plist"
TARGET_DIR="$HOME/Library/LaunchAgents"

echo "🛑 開始卸載 Antigravity LINE Bot 開機自動執行服務..."

if [ -f "$TARGET_DIR/$PLIST_NAME" ]; then
    launchctl unload -w "$TARGET_DIR/$PLIST_NAME" 2>/dev/null || true
    rm -f "$TARGET_DIR/$PLIST_NAME"
    echo "✅ 已成功卸載並停用 automatic Launchd 服務。"
else
    echo "⚠️ 尚未安裝 Launchd 自動執行服務。"
fi
