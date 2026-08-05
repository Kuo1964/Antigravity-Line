#!/usr/bin/env bash
# 今天 17:10 硬體晶片通電開機 ➔ 預留 10 分鐘連網緩衝 ➔ 17:20 發送早安圖至 Private 一鍵測試設定腳本

PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
TODAY_DATE=$(date +"%m/%d/%Y")

echo "============================================================"
echo " 🚀 今日 17:10 硬體自動開機 (緩衝10分鐘) ➔ 17:20 發送 Private 測試 "
echo "============================================================"
echo "▸ 1. 今天 $TODAY_DATE 17:10:00 硬體 RTC 自動通電開機 (poweron)"
echo "▸ 2. macOS 自動登入桌面，預留 10 分鐘讓 Wi-Fi 與 LINE 完成自動登入"
echo "▸ 3. 今天 $TODAY_DATE 17:20:00 定時發送早安圖至 'Private' 群組"
echo "============================================================"

# 1. 預約硬體通電開機 (需要管理員密碼)
echo -e "\n[1/2] 正在預約 macOS 17:10 硬體通電開機..."
echo "請輸入您的 Mac 管理員密碼："

# 清除舊一次性預約
sudo pmset schedule cancelall 2>/dev/null

# 預約 17:10 硬體晶片自動通電開機
sudo pmset schedule poweron "$TODAY_DATE 17:10:00"

# 2. 在 crontab 中寫入 17:20 發送給 Private 的測試排程
echo -e "\n[2/2] 正在配置 17:20 發送至 Private 的測試排程..."

TEST_CRON="20 17 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"Private\" --countdown 1 >> \"$PROJECT_DIR/cron.log\" 2>&1"

(crontab -l 2>/dev/null | grep -v "send_daily_morning_card.py --target \"Private\"" | grep -v "shutdown -h now" | grep -v "pkill -9 iTerm2"; echo "$TEST_CRON") | crontab -

echo "============================================================"
echo " 🎉 17:10 自動開機登入 (預留10分鐘緩衝) ➔ 17:20 發送測試預約設定完成！"
echo "▸ 檢查目前硬體排程："
pmset -g sched
echo "============================================================"
echo "⚠️ 下一步操作說明："
echo "1. 請確保 LINE 當前已登入並勾選『自動登入』。"
echo "2. 請點選 Apple 選單 ➔ 【關機... (Shut Down...)】將電腦完全關閉。"
echo "3. 電腦關閉後，Mac 將會在 17:10 自動通電開機登入，並於 17:20 完成早安圖片發送至 Private！"
echo "============================================================"
