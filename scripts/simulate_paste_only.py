#!/usr/bin/env python3
"""
模擬測試腳本：精確定位 LINE 好友並貼上早安圖片，保留在對話輸入框中，不按 Enter 送出，供人工目視檢查
"""

import os
import sys
import time
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.line_desktop_controller import search_and_send_image
from app.services.image_crawler import fetch_latest_good_morning_image

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger("SimulatePasteOnly")

def main():
    target = "Sophia Kuo"
    logger.info(f"🚀 開始執行模擬貼圖測試 (目標: '{target}')，貼上後絕不送出！")
    
    # 確保有一張圖片
    cached_img = "/tmp/morning_images/morning_latest.jpg"
    if not os.path.exists(cached_img):
        logger.info("未檢測到快取圖片，正在線上下載一張最新早安圖...")
        cached_img = fetch_latest_good_morning_image()
    
    logger.info(f"使用早安圖檔案: {cached_img}")
    
    # 執行 dry_run=True 流程
    success = search_and_send_image(target_name=target, image_path=cached_img, dry_run=True)
    
    if success:
        logger.info("🎯 模擬測試已順利完成！圖片已貼入對話框，游標處於待命狀態。")
    else:
        logger.error("❌ 模擬測試失敗！")

if __name__ == "__main__":
    main()
