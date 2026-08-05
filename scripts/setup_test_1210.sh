#!/usr/bin/env bash
# 今天 12:08 強效關機 ➔ 12:10 硬體晶片通電開機 ➔ 12:12 發送早安圖至 Private 一鍵測試設定腳本

PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
TODAY_DATE=$(date +"%m/%d/%Y")

echo "============================================================"
echo " 🚀 今日 12:08 關機 ➔ 12:10 硬體自動開機發送 Private 測試 "
echo "============================================================"
echo "▸ 1. 今天 $TODAY_DATE 12:08:00 自動強行關閉 iTerm2 (SIGKILL) 並關機 (Shutdown)"
echo "▸ 2. 今天 $TODAY_DATE 12:10:00 硬體 RTC 自動通電開機 (Wakepoweron)"
echo "▸ 3. 今天 $TODAY_DATE 12:12:00 定時發送早安圖至 'Private' 群組"
echo "============================================================"

# 1. 預約關機與硬體通電開機 (需要管理員密碼)
echo -e "\n[1/2] 正在預約 macOS 12:10 硬體通電開機..."
echo "請輸入您的 Mac 管理員密碼："

# 清除舊預約
sudo pmset schedule cancelall 2>/dev/null

# 預約 12:10 硬體晶片自動通電開機
sudo pmset schedule wakepoweron "$TODAY_DATE 12:10:00"

# 2. 在 crontab 中寫入 12:08 強效關閉 iTerm2 關機，以及 12:12 發送給 Private 的測試排程
echo -e "\n[2/2] 正在配置 12:08 強效關機與 12:12 發送至 Private 的測試排程..."

SHUTDOWN_CRON="8 12 * * * pkill -9 iTerm2 2>/dev/null; killall -9 iTerm2 2>/dev/null; sleep 1; sudo shutdown -h now"
TEST_CRON="12 12 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"Private\" --countdown 1 >> \"$PROJECT_DIR/cron.log\" 2>&1"

(crontab -l 2>/dev/null | grep -v "send_daily_morning_card.py --target \"Private\"" | grep -v "shutdown -h now" | grep -v "pkill -9 iTerm2"; echo "$SHUTDOWN_CRON"; echo "$TEST_CRON") | crontab -

echo "============================================================"
echo " 🎉 12:08 關機 ➔ 12:10 開機發送測試預約設定完成！"
echo "▸ 檢查目前硬體排程："
pmset -g sched
echo "============================================================"
echo "⚠️ 注意事項："
echo "1. 請在 12:08 前保存正在編輯的個人文檔。"
echo "2. 12:08 系統會強效關機，12:10 會自動開機通電，12:12 發送至 Private！"
echo "============================================================"
