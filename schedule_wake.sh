#!/bin/bash

# 設定 macOS 電腦每天早上 07:00 自動從睡眠/休眠狀態喚醒 (Wake from Sleep)
# MTWRFSU 代表一週七天 (Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday)

echo "⏰ 正在為 macOS 設定每日 07:00:00 定時硬體喚醒..."
sudo pmset repeat wake MTWRFSU 07:00:00

echo "✅ 喚醒排程設定完成！查看目前喚醒排程："
sudo pmset -g sched
