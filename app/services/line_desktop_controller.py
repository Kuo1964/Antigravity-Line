import os
import time
import logging
from app.services.macos_ui_adapter import MacOSUIAdapter

logger = logging.getLogger(__name__)

def focus_line_app(adapter: MacOSUIAdapter) -> bool:
    """
    開啟、還原並聚焦 macOS 版 LINE 桌面應用程式
    """
    logger.info("正在喚醒並聚焦 LINE 桌面版...")
    try:
        # 1. 喚起主視窗
        adapter.reopen_app("LINE")
        # 2. 確保視窗取消隱藏 (輔助保險機制)
        adapter.unhide_window("LINE")
        return True
    except Exception as e:
        logger.error(f"聚焦 LINE App 異常: {e}")
        return False

def search_and_send_image(target_name: str, image_path: str = "") -> bool:
    """
    在 LINE 桌面版中精確搜尋好友/群組名稱，點選該搜尋結果，並貼上 (Cmd+V) 傳送早安圖片
    """
    logger.info(f"準備使用 MacOSUIAdapter 精確搜尋: '{target_name}'...")
    
    adapter = MacOSUIAdapter()
    
    if not focus_line_app(adapter):
        return False

    try:
        # 1. 取得視窗座標並原生點擊全域搜尋框 (避免 Cmd+F 開啟聊天室內搜尋)
        bounds = adapter.get_window_bounds("LINE")
        if not bounds:
            logger.error("因無法獲取 LINE 視窗真實座標，為了安全起見，終止發送任務。")
            return False
        win_x, win_y, win_w, win_h = bounds
        
        search_x = win_x + 190
        search_y = win_y + 95
        logger.info(f"步驟 A: 原生點擊全域搜尋框座標 ({search_x}, {search_y})")
        adapter.native_click(search_x, search_y)
        time.sleep(1.0)

        # 2. 清空原本的搜尋內容 (Cmd+A, Backspace) 並輸入目標名稱
        logger.info(f"步驟 B: 輸入目標名稱 '{target_name}'")
        adapter.send_keystroke("a", using_cmd=True)
        time.sleep(0.3)
        adapter.send_keycode(51) # Backspace
        time.sleep(0.5)
        adapter.send_keystroke(target_name)
        time.sleep(2.0) # 等待搜尋結果浮現

        # 3. 往下點選搜尋結果清單中的第 1 個結果 (朋友)
        result_item_x = win_x + 220
        result_item_y = win_y + 185
        logger.info(f"步驟 C: 原生實體點擊搜尋結果 '{target_name}' 項目座標 ({result_item_x}, {result_item_y})")
        adapter.native_click(result_item_x, result_item_y)
        time.sleep(1.5) # 等待右側聊天室畫面載入

        # 4. 點選右側聊天室下方的對話輸入框，確保游標在那裡
        chat_input_x = win_x + (win_w // 2) + 100
        chat_input_y = win_y + win_h - 60
        logger.info(f"步驟 D: 原生點擊右側對話框輸入區座標 ({chat_input_x}, {chat_input_y})")
        adapter.native_click(chat_input_x, chat_input_y)
        time.sleep(0.6)

        # 5. 將圖片寫入系統剪貼簿
        if image_path and os.path.exists(image_path):
            from app.services.image_crawler import copy_image_to_clipboard
            logger.info(f"步驟 E: 將早安圖片寫入剪貼簿 ({image_path})...")
            copy_image_to_clipboard(image_path)
            time.sleep(1.0)

        # 6. 貼上並發送 (Cmd + V, Return)
        logger.info("步驟 F: 於目標聊天室貼上早安圖片並發送...")
        adapter.send_keystroke("v", using_cmd=True)
        logger.info("等待 3.5 秒讓 LINE 完整載入圖片預覽...")
        time.sleep(3.5)
        adapter.send_keycode(36) # Return 發送
        time.sleep(2.0)
        
        logger.info(f"成功於 LINE 桌面版向 '{target_name}' 完成早安圖片發送！")
        return True

    except Exception as e:
        logger.error(f"MacOSUIAdapter 操作失敗: {e}")
        return False
