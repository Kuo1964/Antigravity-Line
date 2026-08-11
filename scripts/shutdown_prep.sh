#!/bin/bash
# 關機前準備任務 (退場機制)
LOG_FILE="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/temp/timeline_test.log"
echo "=== $(date) [Shutdown] 準備關機退場任務啟動 ===" >> "$LOG_FILE"

# 1. 優雅關閉 LINE
echo "[Shutdown] 正在關閉 LINE..." >> "$LOG_FILE"
osascript -e 'tell application "LINE" to quit'

# 2. 停止可能佔用資源的背景服務或 IDE
echo "[Shutdown] 正在關閉 Antigravity..." >> "$LOG_FILE"
osascript -e 'tell application "Antigravity" to quit'

echo "=== $(date) [Shutdown] 準備完成，等待系統執行最終關機指令 ===" >> "$LOG_FILE"
