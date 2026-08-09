#!/bin/bash
# 預約測試腳本: setup_test_1200.sh
# 設定今天 12:00:00 自動硬體通電開機，12:05:00 發送 Private，12:03~12:06 畫面錄影

echo "=== 啟動 12:00 自動開機與 12:05 發送測試配置 ==="

# 1. 啟用免密碼 pmset 權限配置 (Sudoers Nopasswd Rule)
SUDOERS_FILE="/etc/sudoers.d/antigravity_pmset"
if [ ! -f "$SUDOERS_FILE" ]; then
    echo "正在設定 pmset 免密碼存取權限..."
    echo "%admin ALL=(ALL) NOPASSWD: /usr/bin/pmset" | sudo tee "$SUDOERS_FILE" >/dev/null
    sudo chmod 0440 "$SUDOERS_FILE"
    echo "✅ 已成功配置 pmset 免密碼權限！"
fi

# 2. 預約今天 12:00:00 硬體通電開機 (Power On)
echo "正在清除舊預約並設定 08/09/2026 12:00:00 通電開機..."
sudo pmset schedule cancelall 2>/dev/null
sudo pmset schedule poweron "08/09/2026 12:00:00"

echo "=== 目前系統硬體預約狀態 (pmset -g sched) ==="
sudo pmset -g sched

# 3. 寫入 12:03~12:06 視訊錄影與 12:05:00 Private 發送任務至 crontab
CRON_LOG="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/cron.log"
PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
REC_FILE="$PROJECT_DIR/temp/test_recording_1200.mp4"

(crontab -l 2>/dev/null | grep -v "send_daily_morning_card.py" | grep -v "screencapture"; \
 echo "3 12 * * * screencapture -v -V 180 -x -C \"$REC_FILE\" >/dev/null 2>&1 &"; \
 echo "5 12 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"Private\" --countdown 1 >> \"$CRON_LOG\" 2>&1"; \
 echo "0 9 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"Sharon Chou\" --countdown 1 >> \"$CRON_LOG\" 2>&1"; \
 echo "30 21 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"郭泊彤\" --countdown 1 >> \"$CRON_LOG\" 2>&1") | crontab -

echo "=== 目前 crontab 排程清單 ==="
crontab -l

echo ""
echo "🎉 12:00 硬體開機與 12:05 發送測試配置成功！"
echo "請您現在點選 Apple 選單 ➔ 【關機... (Shut Down...)】將電腦完全關閉。"
echo "電腦將會在 12:00:00 自動通電開機進入桌面，並於 12:05:00 完成發送！"
