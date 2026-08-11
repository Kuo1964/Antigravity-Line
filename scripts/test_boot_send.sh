#!/bin/bash
# 測試專用：開機延遲啟動與發送腳本
# 此腳本將由 LaunchAgent 在使用者登入後自動觸發

LOG_FILE="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/temp/boot_test_execution.log"
echo "=== $(date) 開機自動化腳本已觸發 ===" >> "$LOG_FILE"

# 1. 系統剛開機，強制等待兩分鐘 (120 秒) 讓網路與常駐程式載入完畢
echo "開始等待 120 秒..." >> "$LOG_FILE"
sleep 120

# 2. 啟動 LINE 應用程式
echo "啟動 LINE App..." >> "$LOG_FILE"
open -a "LINE"

# 3. 啟動 LINE 後，再等待一分鐘 (60 秒) 確保介面與網路連線完成
echo "LINE 已呼叫，再等待 60 秒..." >> "$LOG_FILE"
sleep 60

# 4. 呼叫發送早安圖的 Python 主程式 (目標: Private)
echo "開始呼叫 Python 發送程式 (Private)..." >> "$LOG_FILE"
cd "/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"

# 確保環境變數正確，執行腳本
/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/venv/bin/python scripts/send_daily_morning_card.py --target Private >> "$LOG_FILE" 2>&1

echo "=== $(date) 自動化腳本執行完畢 ===" >> "$LOG_FILE"
