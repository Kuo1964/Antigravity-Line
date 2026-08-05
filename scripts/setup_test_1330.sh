#!/usr/bin/env bash
# 今天 13:28 硬體晶片通電開機 ➔ 13:30 發送早安圖至 Private 排程設定腳本

PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
TODAY_DATE=$(date +"%m/%d/%Y")

echo "============================================================"
echo " 🚀 今日 13:28 硬體開機 ➔ 13:30 發送至 Private 測試 "
echo "============================================================"
echo "▸ 1. 今天 $TODAY_DATE 13:28:00 硬體 RTC 自動通電開機 (Wakepoweron)"
echo "▸ 2. 今天 $TODAY_DATE 13:30:00 定時發送早安圖至 'Private' 群組"
echo "============================================================"

# 1. 預約硬體通電開機 (需要管理員密碼)
echo -e "\n[1/2] 正在預約 macOS 13:28 硬體通電開機..."
echo "請輸入您的 Mac 管理員密碼："

# 清除舊預約
sudo pmset schedule cancelall 2>/dev/null

# 預約 13:28 硬體晶片自動通電開機
sudo pmset schedule wakepoweron "$TODAY_DATE 13:28:00"

# 2. 在 crontab 中寫入 13:30 發送給 Private 的測試排程
echo -e "\n[2/2] 正在配置 13:30 發送至 Private 的測試排程..."

TEST_CRON="30 13 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"Private\" --countdown 1 >> \"$PROJECT_DIR/cron.log\" 2>&1"

(crontab -l 2>/dev/null | grep -v "send_daily_morning_card.py --target \"Private\"" | grep -v "shutdown -h now" | grep -v "pkill -9 iTerm2"; echo "$TEST_CRON") | crontab -

echo "============================================================"
echo " 🎉 13:28 硬體開機 ➔ 13:30 發送測試預約設定完成！"
echo "▸ 檢查目前硬體排程："
pmset -g sched
echo "============================================================"
echo "⚠️ 下一步操作說明："
echo "1. 執行完畢後，請手動關閉各應用程式並將 Mac 電腦進行【關機 (Shutdown)】。"
echo "2. 電腦關機後，請安心離開。Mac 將會在 13:28 自動點亮開機，13:30 自動發送圖片至 Private！"
echo "============================================================"
