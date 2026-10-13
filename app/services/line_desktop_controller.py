import os
import time
import logging
from app.services.macos_ui_adapter import MacOSUIAdapter

logger = logging.getLogger(__name__)

def focus_line_app(adapter: MacOSUIAdapter) -> bool:
    """
    開啟、還原並聚焦 macOS 版 LINE 桌面應用程式 (溫和喚醒，不強殺進程)
    """
    logger.info("正在喚醒並聚焦 LINE 桌面版...")
    try:
        import subprocess
        # 1. 確保應用程式啟動 (open -a LINE 是冪等的，若已啟動則直接喚起)
        subprocess.run(["open", "-a", "LINE"], check=False)
        time.sleep(1.0)
        
        # 2. 透過 AppleScript 執行 activate 與 reopen，確保主視窗展開至前台
        script = '''
        tell application "LINE"
            activate
            reopen
        end tell
        tell application "System Events"
            tell process "LINE"
                set frontmost to true
            end tell
        end tell
        '''
        adapter.execute_applescript(script)
        time.sleep(1.5)
        return True
    except Exception as e:
        logger.error(f"聚焦 LINE App 異常: {e}")
        return False

def search_and_send_image(target_name: str, image_path: str = "", dry_run: bool = False) -> bool:
    """
    在 LINE 桌面版中精確搜尋好友/群組名稱，點選該搜尋結果，並貼上 (Cmd+V) 傳送早安圖片
    :param target_name: 目標名稱
    :param image_path: 圖片檔案路徑
    :param dry_run: 若為 True，則貼上圖片後不按下 Return 送出，供人工目視檢查
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

        # 2. 清空原本的搜尋內容 (Cmd+A, Backspace) 並輸入目標名稱 (優先剪貼簿貼上防掉字)
        logger.info(f"步驟 B: 輸入目標名稱 '{target_name}'")
        adapter.send_keystroke("a", using_cmd=True)
        time.sleep(0.3)
        adapter.send_keycode(51) # Backspace
        time.sleep(0.3)
        adapter.copy_text_to_clipboard(target_name)
        time.sleep(0.3)
        adapter.send_keystroke("v", using_cmd=True)
        time.sleep(1.5) # 等待搜尋結果浮現

        # 3. 按下 Return (Keycode 36) 開啟首項搜尋結果聊天室
        logger.info(f"步驟 C: 送出 Enter 鍵直接開啟 '{target_name}' 聊天室")
        adapter.send_keycode(36) # Return: LINE 直接開啟搜尋結果第一項
        time.sleep(1.5) # 等待聊天室完全載入展開

        # 4. 事先將早安圖片寫入系統剪貼簿，確保貼上時無任何外部行程干擾焦點
        if image_path and os.path.exists(image_path):
            from app.services.image_crawler import copy_image_to_clipboard
            logger.info(f"步驟 D: 將早安圖片事先寫入剪貼簿 ({image_path})...")
            copy_image_to_clipboard(image_path)
            time.sleep(0.5)

        # 5. 原生實體點擊右側對話輸入框中心，緊接著立即貼上圖片，確保絕對對焦
        chat_input_x = win_x + (win_w // 2) + 120
        chat_input_y = win_y + win_h - 70
        logger.info(f"步驟 E: 原生點擊右側對話框輸入區核心座標 ({chat_input_x}, {chat_input_y})，鎖定對焦 🎯")
        adapter.native_click(chat_input_x, chat_input_y)
        time.sleep(0.3)

        # 6. 貼上並發送 (Cmd + V, Return)
        logger.info("步驟 F: 於目標聊天室立即貼上早安圖片 (Cmd+V)...")
        adapter.send_keystroke("v", using_cmd=True)
        logger.info("等待 3.5 秒讓 LINE 完整載入圖片預覽...")
        time.sleep(3.5)
        
        if not dry_run:
            adapter.send_keycode(36) # Return 發送
            time.sleep(2.0)
            logger.info(f"成功於 LINE 桌面版向 '{target_name}' 完成早安圖片發送！")
        else:
            logger.info(f"⚠️ [模擬測試模式] 已將早安圖片貼入 '{target_name}' 聊天室，未按下發送，保留供目視檢查！")
            
        return True

    except Exception as e:
        logger.error(f"MacOSUIAdapter 操作失敗: {e}")
        return False
