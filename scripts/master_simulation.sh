#!/bin/bash
# 10 分鐘雙時區自動化主控演練腳本 (V8.1 全自動化版)

LOG_FILE="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/temp/timeline_test.log"
echo "=================================================" >> "$LOG_FILE"
echo "=== $(date) 主控演練腳本啟動 (自動登入後) ===" >> "$LOG_FILE"
echo "=================================================" >> "$LOG_FILE"

# 1. 靜默等待 2 分鐘，讓系統與常駐程式準備好
echo ">>> [T=0] 開始等待 2 分鐘 <<<" >> "$LOG_FILE"
sleep 120

# 2. 開啟應用程式並等待 30 秒
echo ">>> [T=2] 啟動 LINE 與 Antigravity，等待 30 秒 <<<" >> "$LOG_FILE"
open -a "LINE"
open -a "Antigravity" || echo "[Warning] 找不到 Antigravity 應用程式" >> "$LOG_FILE"
sleep 30

# 3. 執行早晨發送任務
echo ">>> [T=2.5] 執行早晨發送任務 <<<" >> "$LOG_FILE"
cd "/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
venv/bin/python scripts/send_daily_morning_card.py --target Private >> "$LOG_FILE" 2>&1

# 4. 強制進入鎖定 (模擬休眠)
echo ">>> [T=3.5] 早晨發送完畢。強制鎖定螢幕 (Ctrl+Cmd+Q)... <<<" >> "$LOG_FILE"
osascript -e 'tell application "System Events" to keystroke "q" using {control down, command down}'
echo ">>> 腳本進入背景，模擬夜晚等待 150 秒 (加上 caffeinate 確保腳本不休眠) <<<" >> "$LOG_FILE"
caffeinate -i sleep 150

# 5. 喚醒並執行夜間發送任務
echo ">>> [T=5.5] 喚醒系統，準備執行夜間發送任務 <<<" >> "$LOG_FILE"
caffeinate -u -t 2 &
sleep 2
venv/bin/python scripts/send_daily_morning_card.py --target Private >> "$LOG_FILE" 2>&1

# 5.5. 發送完畢後，等待 5 分鐘供使用者驗屍與檢查
echo ">>> [T=6] 夜間發送完畢，腳本暫停 5 分鐘 (300 秒) 供您檢查結果與圖片 <<<" >> "$LOG_FILE"
caffeinate -i sleep 300

# 6. 刪除本次測試的排程檔 (只刪除檔案，不 unload，避免腳本被系統強制中止)
echo ">>> [T=11] 刪除測試排程 (LaunchAgent) 檔案，確保下次開機不再執行 <<<" >> "$LOG_FILE"
rm -f "$HOME/Library/LaunchAgents/com.antigravity.boottest.plist"

# 7. 關機前退場準備 (關閉應用程式)
echo ">>> [T=11] 執行關機前優雅退場任務 (關閉 LINE 與 Antigravity) <<<" >> "$LOG_FILE"
osascript -e 'tell application "LINE" to quit'
osascript -e 'tell application "Antigravity" to quit'
sleep 5

echo "=================================================" >> "$LOG_FILE"
echo "=== $(date) 主控演練腳本全部完成，正在執行系統自動關機 ===" >> "$LOG_FILE"
echo "=================================================" >> "$LOG_FILE"

# 8. 執行系統自動關機
osascript -e 'tell application "System Events" to shut down'
