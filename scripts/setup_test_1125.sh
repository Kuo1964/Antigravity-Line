#!/usr/bin/env bash
# 今天 11:20 硬體開機 ➔ 11:25 發送早安圖至 Private ➔ 11:26 開啟 Antigravity 一鍵測試設定腳本

PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
TODAY_DATE=$(date +"%m/%d/%Y")

echo "============================================================"
echo " 🚀 今日 11:20 開機 ➔ 11:25 發送 Private ➔ 11:26 開啟 Antigravity 測試 "
echo "============================================================"
echo "▸ 1. 今天 $TODAY_DATE 11:20:00 硬體 RTC 自動通電開機 (poweron)"
echo "▸ 2. 今天 $TODAY_DATE 11:25:00 定時發送早安圖至 'Private' 群組"
echo "▸ 3. 今天 $TODAY_DATE 11:26:00 自動開啟 Antigravity 應用程式"
echo "============================================================"

# 1. 預約硬體通電開機 (需要管理員密碼)
echo -e "\n[1/3] 正在預約 macOS 11:20 硬體通電開機..."
echo "請輸入您的 Mac 管理員密碼："

# 清除舊一次性預約
sudo pmset schedule cancelall 2>/dev/null

# 預約 11:20 硬體晶片自動通電開機
sudo pmset schedule poweron "$TODAY_DATE 11:20:00"

# 2. 在 crontab 中寫入 11:25 發送 Private 與 11:26 開啟 Antigravity 的測試排程
echo -e "\n[2/3] 正在配置 11:25 發送至 Private 與 11:26 開啟 Antigravity 排程..."

SEND_CRON="25 11 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"Private\" --countdown 1 >> \"$PROJECT_DIR/cron.log\" 2>&1"
OPEN_AGY_CRON="26 11 * * * open -a \"Antigravity\" 2>/dev/null || open -a \"Google Antigravity\" 2>/dev/null"

(crontab -l 2>/dev/null | grep -v "send_daily_morning_card.py --target \"Private\"" | grep -v "shutdown -h now" | grep -v "pkill -9 iTerm2" | grep -v "open -a \"Antigravity\""; echo "$SEND_CRON"; echo "$OPEN_AGY_CRON") | crontab -

echo "============================================================"
echo " 🎉 11:20 開機 ➔ 11:25 發送 ➔ 11:26 開啟 Antigravity 預約設定完成！"
echo "▸ 檢查目前硬體排程："
pmset -g sched
echo "============================================================"
echo "⚠️ 下一步操作說明："
echo "1. 請點選 Apple 選單 ➔ 【關機... (Shut Down...)】將電腦完全關閉。"
echo "2. 電腦關閉後，Mac 將在 11:20 自動開機登入，11:25 發送圖片至 Private，11:26 自動開啟 Antigravity！"
echo "============================================================"
