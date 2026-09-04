#!/bin/bash
# PROTOTYPE - E2E 鎖定發送測試腳本

echo "=== Prototype: E2E Full Flow Test ==="

echo "[1/4] 模擬系統鎖定 (關閉顯示器並鎖定)..."
pmset displaysleepnow
echo "等待 10 秒讓系統確實進入鎖定狀態..."
sleep 10

echo "[2/4] 觸發第一次早安圖片發送 (目標: Private)..."
PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target Private

echo "[3/4] 第一次發送完畢。腳本應已自動恢復鎖定狀態。"
echo "等待 15 秒以驗證鎖定狀態並準備下一次發送..."
sleep 15

echo "[4/4] 觸發第二次早安圖片發送 (目標: Private)..."
PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target Private

echo "=== 測試腳本執行完畢 ==="
