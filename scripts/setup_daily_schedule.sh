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
echo -e "\n[1/3] 正在設定 macOS 硬體喚醒時間 (每日 08:58 與 21:28)..."
echo "若系統要求，請輸入您的 Mac 管理員密碼："
sudo pmset repeat wake MTWRFSU 08:58:00,21:28:00

# 2. 安裝與載入 macOS launchd 重開機自動啟動守護服務 (LaunchAgent)
echo -e "\n[2/3] 正在配置 macOS 開機自動啟動服務 (LaunchAgent)..."
mkdir -p "$HOME/Library/LaunchAgents"
cp "$PROJECT_DIR/scripts/com.antigravity.linebridge.plist" "$HOME/Library/LaunchAgents/"
launchctl unload "$HOME/Library/LaunchAgents/com.antigravity.linebridge.plist" 2>/dev/null
launchctl load -w "$HOME/Library/LaunchAgents/com.antigravity.linebridge.plist"
echo "▸ 已成功將 Antigravity Line Bridge 服務註冊為 macOS 重開機自動啟動守護程式 (KeepAlive: ON)"

# 3. 自動配置 crontab 每日發送與重開機自我修復
echo -e "\n[3/3] 正在配置 macOS crontab 每日定時發送與重開機任務..."

CRON_JOB_1="0 9 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"Sharon Chou\" --countdown 1 >> \"$PROJECT_DIR/cron.log\" 2>&1"
CRON_JOB_2="30 21 * * * cd \"$PROJECT_DIR\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"郭泊彤\" --countdown 1 >> \"$PROJECT_DIR/cron.log\" 2>&1"
CRON_REBOOT="@reboot cd \"$PROJECT_DIR\" && launchctl load -w \"$HOME/Library/LaunchAgents/com.antigravity.linebridge.plist\" 2>/dev/null"

# 備份原有 crontab 並追加新任務 (避開重複)
(crontab -l 2>/dev/null | grep -v "send_daily_morning_card.py" | grep -v "test_private_lock_send.py" | grep -v "com.antigravity.linebridge"; echo "$CRON_JOB_1"; echo "$CRON_JOB_2"; echo "$CRON_REBOOT") | crontab -

echo "============================================================"
echo " 🎉 全套自動化部署設定完成！"
echo "▸ 1. macOS 硬體自動喚醒：每日 08:58 與 21:28"
echo "▸ 2. 每日雙時區定時發送：09:00 (Sharon Chou), 21:30 (郭泊彤)"
echo "▸ 3. 開機自動啟動：已登錄 launchd 守護服務，每次重新開機自動在背景啟動！"
echo "============================================================"

