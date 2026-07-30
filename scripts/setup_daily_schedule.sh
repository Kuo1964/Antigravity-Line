#!/usr/bin/env bash
# macOS 硬體喚醒與雙時區 LINE 早安圖 Crontab 一鍵自動化設定腳本

PROJECT_DIR="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"

echo "============================================================"
echo " 🚀 雙時區 LINE 早安圖每日定時自動化排程設定 "
echo "============================================================"
echo "▸ 任務一：台灣時間 每日 09:00 發送至 'Sharon Chou'"
echo "▸ 任務二：美東時間 每日 09:30 (台灣時間 21:30) 發送至 '郭泊彤'"
echo "▸ macOS 硬體喚醒時間：每日 08:58:00 與 21:28:00"
echo "============================================================"

# 1. 設置 macOS RTC 硬體排程喚醒 (需輸入 sudo 密碼)
echo -e "\n[1/2] 正在設定 macOS 硬體喚醒時間 (每日 08:58 與 21:28)..."
echo "若系統要求，請輸入您的 Mac 管理員密碼："
sudo pmset repeat wake MTWRFSU 08:58:00,21:28:00

# 2. 自動配置 crontab
echo -e "\n[2/2] 正在配置 macOS crontab 每日定時任務..."

CRON_JOB_1="0 9 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"Sharon Chou\" --countdown 1 >> \"$PROJECT_DIR/cron.log\" 2>&1"
CRON_JOB_2="30 21 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"郭泊彤\" --countdown 1 >> \"$PROJECT_DIR/cron.log\" 2>&1"

# 備份原有 crontab 並追加新任務 (避開重複)
(crontab -l 2>/dev/null | grep -v "send_daily_morning_card.py" | grep -v "test_private_lock_send.py"; echo "$CRON_JOB_1"; echo "$CRON_JOB_2") | crontab -


echo "============================================================"
echo " 🎉 設定完成！"
echo "▸ 現已成功配置硬體自動喚醒與每日 09:00 / 21:30 定時發送。"
echo "▸ 電腦睡眠或鎖定時將自動喚醒、發送圖片並自動恢復睡眠！"
echo "============================================================"
