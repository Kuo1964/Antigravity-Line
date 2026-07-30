import os
import time
import logging
from typing import Dict, Any

from app.services.mac_unlocker import unlock_mac, detect_mac_screen_state, restore_mac_screen_state
from app.services.image_crawler import fetch_latest_good_morning_image, copy_image_to_clipboard
from app.services.line_desktop_controller import search_and_send_image

logger = logging.getLogger(__name__)

def run_good_morning_workflow(target_name: str = "Private", mac_password: str = "") -> Dict[str, Any]:
    """
    執行完整的早安圖片自動發送工作流程，並於發送完成後自動恢復發送前的螢幕狀態 (鎖定/睡眠或開啟)
    :param target_name: 目標 LINE 好友或群組名稱 (預設: 'Private')
    :param mac_password: macOS 解鎖密碼 (可選)
    :return: 執行結果狀態字典
    """
    logger.info(f"=== 開始發送早安圖工作流程 (目標: {target_name}) ===")
    
    # 0. 檢測並記錄發送前 Mac 的原始螢幕狀態
    initial_state = detect_mac_screen_state()
    
    result = {
        "success": False,
        "target": target_name,
        "image_path": "",
        "message": ""
    }

    try:
        # 1. 解鎖 macOS 螢幕
        logger.info("步驟 1/4: 解鎖與喚醒 macOS 螢幕...")
        unlock_mac(mac_password)
        time.sleep(1.5)

        # 2. 下載當日最新早安圖片
        logger.info("步驟 2/4: 上網抓取當日最新祝賀早安圖...")
        try:
            image_path = fetch_latest_good_morning_image()
            result["image_path"] = image_path
        except Exception as e:
            msg = f"抓取早安圖失敗: {e}"
            logger.error(msg)
            result["message"] = msg
            return result

        # 3. 將圖片寫入 macOS 系統剪貼簿
        logger.info("步驟 3/4: 將圖片複製入 macOS 剪貼簿...")
        if not copy_image_to_clipboard(image_path):
            msg = "圖片寫入剪貼簿失敗"
            result["message"] = msg
            return result

        # 4. LINE 桌面版搜尋目標並發送
        logger.info(f"步驟 4/4: 開啟 LINE 桌面版並發送至 '{target_name}'...")
        if search_and_send_image(target_name, image_path):
            result["success"] = True
            result["message"] = f"成功發送早安圖給 LINE 的 '{target_name}'！"
            logger.info(result["message"])
        else:
            result["message"] = f"發送至 LINE '{target_name}' 失敗，請確認桌面版 LINE 已開啟與權限。"
            logger.error(result["message"])

    finally:
        # 5. 無論成功或異常，均自動將 macOS 螢幕恢復至執行前的原始狀態！
        logger.info("步驟 5/5: 正在將 macOS 螢幕恢復至發送前狀態...")
        restore_mac_screen_state(initial_state)

    return result

