#!/usr/bin/env python3
"""
正式版本：LINE 電腦版自動發送當日祝賀早安圖
支援休眠/鎖定自動喚醒、解鎖、精確發送，與發送後自動復原睡眠鎖定狀態。
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.scheduler_service import run_good_morning_workflow

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("SendDailyMorningCard")

def main():
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="正式版 LINE 每日早安圖片自動發送")
    parser.add_argument("--target", required=True, help="目標 LINE 好友或群組名稱 (例如: 'Sharon Chou' 或 '郭泊彤')")
    parser.add_argument("--countdown", type=int, default=1, help="觸發前的等待緩衝秒數 (預設: 1 秒)")
    args = parser.parse_args()

    mac_password = os.getenv("MAC_PASSWORD", "")

    logger.info(f"=== 啟動正式版早安發送任務 (目標: '{args.target}') ===")
    
    res = run_good_morning_workflow(target_name=args.target, mac_password=mac_password)

    if res["success"]:
        logger.info(f"🎉 正式發送任務成功！早安圖片已成功送達 '{args.target}'！")
    else:
        logger.error(f"❌ 正式發送任務失敗: {res['message']}")

if __name__ == "__main__":
    main()
