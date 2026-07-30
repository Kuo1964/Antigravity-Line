#!/usr/bin/env python3
"""
鎖定狀態端到端測試腳本：
測試於 macOS 鎖定狀況下，自動解鎖螢幕、抓取最新早安圖，並發送至 LINE 指定目標 (預設: 'Private' 群組)。
"""

import os
import sys
import time
import argparse
import logging
from dotenv import load_dotenv

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.scheduler_service import run_good_morning_workflow

# 設定日誌格式
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("TestPrivateLockSend")

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="LINE 電腦版鎖定狀態早安圖發送測試")
    parser.add_argument("--target", default="Private", help="目標 LINE 好友或群組名稱 (預設: Private)")
    parser.add_argument("--countdown", type=int, default=10, help="鎖定測試倒數秒數 (預設: 10 秒)")
    args = parser.parse_args()

    mac_password = os.getenv("MAC_PASSWORD", "")

    print("\n" + "="*60)
    print(" 🚀 LINE 電腦版鎖定狀態早安圖測試啟動 ")
    print("="*60)
    print(f"▸ 測試目標群組/好友: '{args.target}'")
    print(f"▸ macOS 密碼設定: {'[已設定]' if mac_password else '[未設定 - 請確認 .env 中的 MAC_PASSWORD]'}")
    print(f"▸ 倒數計時: {args.countdown} 秒")
    print("="*60)
    print("\n⚠️ 【請注意】請立刻按下 Ctrl + Cmd + Q 鎖定您的 macOS 螢幕！")
    print("倒數計時即將開始...\n")

    for i in range(args.countdown, 0, -1):
        print(f"⏱️ 距離測試觸發還剩: {i} 秒 (請鎖定螢幕)...", end="\r")
        time.sleep(1)

    print("\n\n🔔 倒數結束！開始執行自動解鎖與 LINE 發送工作流程...\n")

    res = run_good_morning_workflow(target_name=args.target, mac_password=mac_password)

    print("\n" + "="*60)
    if res["success"]:
        print(" 🎉 測試成功！早安圖片已順利發送！")
        print(f" ▸ 發送目標: {res['target']}")
        print(f" ▸ 圖片路徑: {res['image_path']}")
    else:
        print(" ❌ 測試失敗！")
        print(f" ▸ 失敗原因: {res['message']}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
