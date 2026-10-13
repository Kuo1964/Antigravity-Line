#!/usr/bin/env python3
"""
鎖定螢幕下的模擬測試腳本：
1. 提供 12 秒緩衝倒數，讓使用者手動鎖定 Mac 畫面 (Ctrl+Cmd+Q)
2. 自動發送喚醒訊號 (caffeinate) 並安全解鎖 loginwindow
3. 聚焦 LINE 桌面版，搜尋目標好友 'Sophia Kuo'
4. 貼上早安圖片至對話輸入框，保留待命狀態 (不按 Enter 送出)
5. 截圖存證供使用者目視核對
"""

import os
import sys
import time
import logging
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.scheduler_service import run_good_morning_workflow

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("SimulateLockedPaste")

def main():
    load_dotenv()
    target = "Sophia Kuo"
    mac_password = os.getenv("MAC_PASSWORD", "")
    delay = 20

    logger.info("==================================================================")
    logger.info(f" 🔒 準備進行「鎖定螢幕下」的模擬測試 (目標: '{target}')")
    logger.info(f" 倒數 {delay} 秒，請現在手動鎖定您的 Mac 螢幕 (例如按 Ctrl + Cmd + Q)...")
    logger.info("==================================================================")

    for remaining in range(delay, 0, -1):
        logger.info(f"⏳ 距離啟動喚醒解鎖程序還剩 {remaining} 秒... (請確保已鎖定螢幕)")
        time.sleep(1)

    logger.info("⏰ 倒數結束！開始進入自動喚醒、解鎖與模擬貼圖工作流程...")
    
    res = run_good_morning_workflow(target_name=target, mac_password=mac_password, dry_run=True)

    if res["success"]:
        logger.info("🎉 鎖定狀態下的模擬測試成功完成！圖片已安全貼入對話輸入框！")
    else:
        logger.error(f"❌ 模擬測試失敗: {res.get('message')}")

if __name__ == "__main__":
    main()
