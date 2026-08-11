#!/bin/bash
# 夜間發送與解鎖任務
LOG_FILE="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/temp/timeline_test.log"
echo "=== $(date) [Night] 夜間任務啟動 ===" >> "$LOG_FILE"

# 1. 喚醒螢幕
echo "[Night] 喚醒螢幕..." >> "$LOG_FILE"
caffeinate -u -t 2 &
sleep 1

# (解鎖邏輯已移交至核心 Python 腳本 mac_unlocker.py 統一智慧處理)
# 等待 15 秒讓網路與系統甦醒
echo "[Night] 等待 15 秒確保系統與網路就緒..." >> "$LOG_FILE"
sleep 15

# 3. 呼叫 Python 發送程式 (目標: Private)
echo "[Night] 執行發送腳本 (Private)..." >> "$LOG_FILE"
cd "/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
venv/bin/python scripts/send_daily_morning_card.py --target Private >> "$LOG_FILE" 2>&1

echo "=== $(date) [Night] 夜間任務完成 ===" >> "$LOG_FILE"
