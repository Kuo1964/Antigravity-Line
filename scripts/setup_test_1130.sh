#!/usr/bin/env bash
# macOS 自動關機 (防止 iTerm 阻擋) ➔ 硬體 RTC 晶片開機 ➔ 11:30 發送早安圖至 Private 排程設定腳本

PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
TODAY_DATE=$(date +"%m/%d/%Y")

echo "============================================================"
echo " 🚀 macOS 強效自動關機 ➔ 11:30 硬體開機發送 Private 測試 "
echo "============================================================"

# 1. 設置 11:00 自動優雅關閉 iTerm 並執行強效關機
echo -e "\n[1/2] 正在預約 macOS 11:00 強效關機與 11:28 硬體通電開機..."
echo "請輸入您的 Mac 管理員密碼："

# 取消先前的舊預約
sudo pmset schedule cancelall 2>/dev/null

# 預約 11:28 硬體晶片自動通電開機
sudo pmset schedule wakepoweron "$TODAY_DATE 11:28:00"

# 在 crontab 中加入 11:00 自動關閉 iTerm 並關機的命令
SHUTDOWN_CRON="0 11 * * * osascript -e 'tell application \"iTerm\" to quit' 2>/dev/null; sleep 2; sudo shutdown -h now"
TEST_CRON="30 11 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"Private\" --countdown 1 >> \"$PROJECT_DIR/cron.log\" 2>&1"

(crontab -l 2>/dev/null | grep -v "send_daily_morning_card.py --target \"Private\"" | grep -v "shutdown -h now"; echo "$SHUTDOWN_CRON"; echo "$TEST_CRON") | crontab -

echo "============================================================"
echo " 🎉 測試預約設定完成！"
echo "▸ 已完成 11:00 強效關機 (含 iTerm 自動關閉) 與 11:28 硬體喚醒設定。"
echo "▸ 檢查目前硬體排程："
pmset -g sched
echo "============================================================"
