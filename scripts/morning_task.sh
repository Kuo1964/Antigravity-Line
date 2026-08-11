#!/bin/bash
# 早晨發送任務
LOG_FILE="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/temp/timeline_test.log"
echo "=== $(date) [Morning] 早晨開機任務啟動 ===" >> "$LOG_FILE"

# 等待 120 秒
echo "[Morning] 等待 120 秒，讓網路與系統常駐載入..." >> "$LOG_FILE"
sleep 120

# 啟動 LINE App 與 Antigravity
echo "[Morning] 啟動 LINE App 與 Antigravity..." >> "$LOG_FILE"
open -a "LINE"
# 如果您的應用程式叫 Antigravity，請確認名稱是否精確 (有時叫 Antigravity IDE)
open -a "Antigravity" || echo "[Morning] 找不到 Antigravity 應用程式" >> "$LOG_FILE"

# 等待 60 秒
echo "[Morning] 等待 60 秒確保介面就緒..." >> "$LOG_FILE"
sleep 60

# 呼叫 Python 發送程式 (目標: Private)
echo "[Morning] 執行發送腳本 (Private)..." >> "$LOG_FILE"
cd "/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
venv/bin/python scripts/send_daily_morning_card.py --target Private >> "$LOG_FILE" 2>&1

echo "=== $(date) [Morning] 早晨任務完成 ===" >> "$LOG_FILE"
