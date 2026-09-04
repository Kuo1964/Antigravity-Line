#!/bin/bash

# ==============================================================================
# 螢幕側錄監控腳本
# 用途: 定時或手動啟動，錄製 Mac 螢幕畫面，以監控自動化排程是否正常運作。
# ==============================================================================

# 設定錄影時間 (預設 60 秒)
DURATION=${1:-60}

# 產生的檔案名稱 (帶時間戳記)
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
OUTPUT_DIR="/tmp/morning_images"
OUTPUT_FILE="${OUTPUT_DIR}/monitor_${TIMESTAMP}.mp4"

mkdir -p "${OUTPUT_DIR}"

echo "[$(date)] 開始螢幕錄影，預計錄製 ${DURATION} 秒..."
echo "[$(date)] 儲存路徑: ${OUTPUT_FILE}"

# -v: 錄影模式
# -V: 指定錄影秒數
# -x: 靜音 (不發出快門聲)
screencapture -v -V "${DURATION}" -x "${OUTPUT_FILE}"

echo "[$(date)] 錄影完成！影片已存檔於 ${OUTPUT_FILE}"
