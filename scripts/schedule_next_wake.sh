#!/usr/bin/env bash
# 喚醒接力腳本：自動計算並設定下一次的單次系統喚醒 (pmset schedule wake)
# 此腳本由 Root Crontab 自動呼叫

TARGET_TIME="$1"
if [ -z "$TARGET_TIME" ]; then
    echo "[Error] 必須提供目標時間。範例: $0 \"21:28:00\""
    exit 1
fi

# 取得現在的 epoch 與目標時間今天的 epoch
CURRENT_EPOCH=$(date +%s)
TODAY_TARGET_EPOCH=$(date -j -f "%H:%M:%S" "$TARGET_TIME" +%s 2>/dev/null)

if [ -z "$TODAY_TARGET_EPOCH" ]; then
    echo "[Error] 時間格式解析失敗，請確認格式為 HH:MM:SS"
    exit 1
fi

# 如果現在時間已經過 (或等於) 了今天的目標時間，代表要設定為「明天」
if [ "$CURRENT_EPOCH" -ge "$TODAY_TARGET_EPOCH" ]; then
    WAKE_DATE=$(date -v+1d +"%m/%d/%Y")
else
    # 否則設定為「今天」
    WAKE_DATE=$(date +"%m/%d/%Y")
fi

echo "================================================="
echo "[$(date)] 執行喚醒接力任務..."
echo ">>> 設定下一次硬體喚醒時間為: $WAKE_DATE $TARGET_TIME"

# 執行系統喚醒設定 (必須在 root 權限下)
pmset schedule wake "$WAKE_DATE $TARGET_TIME"

echo ">>> 目前的排程狀態:"
pmset -g sched
echo "================================================="
