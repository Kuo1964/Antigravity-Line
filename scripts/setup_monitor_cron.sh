#!/bin/bash
# 新增監控程式至 crontab，設定為每日 21:35 執行

SCRIPT_PATH="/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/scripts/monitor_log_analyzer.py"

# 檢查是否已經在 crontab 中
crontab -l | grep -q "$SCRIPT_PATH"
if [ $? -eq 0 ]; then
    echo "監控排程已存在於 crontab 中。"
else
    # 備份並寫入新的 crontab
    (crontab -l 2>/dev/null; echo "35 21 * * * $SCRIPT_PATH") | crontab -
    echo "已成功將監控排程新增至 crontab，預計每日 21:35 執行。"
fi
