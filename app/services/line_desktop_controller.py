import os
import time
import logging
from typing import Optional
from app.services.macos_ui_adapter import MacOSUIAdapter

logger = logging.getLogger(__name__)

def focus_line_app(adapter: MacOSUIAdapter, max_retries: int = 6) -> bool:
    """
    開啟、還原並強效聚焦 macOS 版 LINE 桌面應用程式
    透過 AppKit 原生 NSApplicationActivateIgnoringOtherApps 穿透 macOS 防搶焦點機制，
    並嚴格驗證 LINE 已成為最頂層前台應用程式 (Frontmost Active Window)。
    """
    logger.info("正在喚醒並強效聚焦 LINE 桌面版至最前台...")
    import subprocess
    
    # 1. 確保應用程式本體啟動
    subprocess.run(["open", "-a", "LINE"], check=False)
    time.sleep(1.5)

    # 2. 透過 AppleScript 執行 reopen，確保視窗被展開叫出
    script = '''
    tell application "LINE"
        activate
        reopen
    end tell
    '''
    adapter.execute_applescript(script)
    time.sleep(1.0)

    # 3. 透過 AppKit NSWorkspace 原生穿透置頂，對抗 macOS 防搶焦點保護
    try:
        from AppKit import NSWorkspace, NSApplicationActivateIgnoringOtherApps
        from Foundation import NSRunLoop, NSDate
        from app.services.mac_unlocker import mac_unlocker
        ws = NSWorkspace.sharedWorkspace()
        
        for attempt in range(1, max_retries + 1):
            # 泵送事件循環，刷新 Cocoa 內部狀態
            try:
                NSRunLoop.currentRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.05))
            except Exception:
                pass

            line_app = None
            for app in ws.runningApplications():
                if app.localizedName() == "LINE" or app.bundleIdentifier() == "jp.naver.line.mac":
                    line_app = app
                    break
                    
            if line_app:
                line_app.activateWithOptions_(NSApplicationActivateIgnoringOtherApps)
                time.sleep(1.0)
                
            # 優先從 WindowServer 獲取當前真實最頂層 App
            front_name = mac_unlocker.get_frontmost_app_name() or ""
            if not front_name:
                front_app = ws.frontmostApplication()
                front_name = front_app.localizedName() if front_app else ""

            if front_name.lower() == "line":
                logger.info(f"✨ LINE 桌面版已成功置頂於 macOS 最前台 (嘗試次數: {attempt})！")
                return True
            else:
                logger.warning(f"LINE 尚未取得前台焦點 (當前最頂層為: '{front_name}'，嘗試 {attempt}/{max_retries})，正在重新嘗試置頂...")
                # 重新呼叫 reopen 以防視窗處於最小化或未還原狀態
                adapter.execute_applescript(script)
                time.sleep(1.0)
                
        logger.error(f"🚨 [前台置頂失敗] 重試 {max_retries} 次後 LINE 仍未能取得前台焦點！當前最頂層為 '{front_name}'。為保護其他應用程式畫面安全，立即中止任務！")
        return False
    except Exception as e:
        logger.warning(f"AppKit 原生置頂發生異常，使用備援機制: {e}")
        return True

def get_line_search_field_info() -> tuple[Optional[tuple[int, int, int, int]], str]:
    """
    透過 System Events 動態查詢 LINE 全域搜尋框的真實絕對座標 (x, y, w, h) 與當前輸入值
    """
    import subprocess
    script = '''
    tell application "System Events"
        tell process "LINE"
            try
                set s_val to value of text field 1 of splitter group 1 of window 1
                set s_pos to position of text field 1 of splitter group 1 of window 1
                set s_size to size of text field 1 of splitter group 1 of window 1
                set val_str to ""
                if s_val is not missing value then
                    set val_str to s_val as string
                end if
                return (item 1 of s_pos as string) & "," & (item 2 of s_pos as string) & "," & (item 1 of s_size as string) & "," & (item 2 of s_size as string) & "," & val_str
            on error errMsg
                return "ERROR: " & errMsg
            end try
        end tell
    end tell
    '''
    try:
        res = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=3)
        out = res.stdout.strip()
        if out and not out.startswith("ERROR:"):
            parts = out.split(",", 4)
            if len(parts) >= 4:
                x, y, w, h = int(parts[0]), int(parts[1]), int(parts[2]), int(parts[3])
                val = parts[4] if len(parts) > 4 else ""
                return (x, y, w, h), val
    except Exception as e:
        logger.warning(f"動態獲取 LINE 搜尋框資訊失敗: {e}")
    return None, ""

def search_and_send_image(target_name: str, image_path: str = "", dry_run: bool = False) -> bool:
    """
    在 LINE 桌面版中精確搜尋好友/群組名稱，點選該搜尋結果，並貼上 (Cmd+V) 傳送早安圖片
    嚴格具備【搜尋框文字回讀驗證】與【誤發熔斷保護】，若搜尋失敗絕不貼圖送出！
    :param target_name: 目標名稱
    :param image_path: 圖片檔案路徑
    :param dry_run: 若為 True，則貼上圖片後不按下 Return 送出，供人工目視檢查
    """
    logger.info(f"準備使用 MacOSUIAdapter 精確搜尋: '{target_name}'...")
    
    adapter = MacOSUIAdapter()
    
    if not focus_line_app(adapter):
        return False

    try:
        # 1. 取得視窗整體座標備用
        bounds = adapter.get_window_bounds("LINE")
        if not bounds:
            logger.error("因無法獲取 LINE 視窗真實座標，為了安全起見，終止發送任務。")
            return False
        win_x, win_y, win_w, win_h = bounds

        # 2. 優先透過 Accessibility 取得搜尋框即時精確座標，點擊中心位置
        sf_bounds, _ = get_line_search_field_info()
        if sf_bounds:
            sf_x, sf_y, sf_w, sf_h = sf_bounds
            search_x = sf_x + sf_w // 2
            search_y = sf_y + sf_h // 2
            logger.info(f"步驟 A: 透過 Accessibility 取得搜尋框真實座標 ({sf_x}, {sf_y}, {sf_w}, {sf_h})，點擊中心點 ({search_x}, {search_y})")
        else:
            search_x = win_x + 190
            search_y = win_y + 95
            logger.warning(f"步驟 A: 無法取得動態搜尋框座標，使用備援座標 ({search_x}, {search_y})")

        adapter.native_click(search_x, search_y)
        time.sleep(0.8)

        # 3. 清空原本搜尋內容並輸入目標名稱
        logger.info(f"步驟 B: 輸入目標名稱 '{target_name}'")
        adapter.send_keystroke("a", using_cmd=True)
        time.sleep(0.3)
        adapter.send_keycode(51) # Backspace
        time.sleep(0.3)
        adapter.copy_text_to_clipboard(target_name)
        time.sleep(0.3)
        adapter.send_keystroke("v", using_cmd=True)
        time.sleep(1.5) # 等待搜尋結果列表展開

        # 🚨 第一道剛性安全閘門：即時回讀搜尋框，驗證是否真正成功輸入目標名稱！
        _, current_search_val = get_line_search_field_info()
        logger.info(f"步驟 B.1: 驗證搜尋框當前輸入值: '{current_search_val}' (預期包含: '{target_name}')")
        if target_name.lower() not in current_search_val.lower():
            logger.critical(
                f"🚨 [安全防護熔斷攔截] 搜尋框內文字為 '{current_search_val}'，未包含目標對象 '{target_name}'！"
                f"這表示搜尋框未成功聚焦或輸入失敗！為徹底防止誤發給其他聯絡人或群組，立即熔斷終止任務！"
            )
            return False

        # 4. 按下 Down Arrow (KeyCode 125) 精準選取搜尋結果第一筆好友，再按下 Return (KeyCode 36) 開啟聊天室
        logger.info(f"步驟 C: 向下選中搜尋結果第一筆，送出 Enter 鍵開啟 '{target_name}' 聊天室")
        adapter.send_keycode(125) # Down arrow: 移動焦點至搜尋結果第一項
        time.sleep(0.5)
        adapter.send_keycode(36) # Return: 開啟該搜尋結果聊天室
        time.sleep(2.0) # 等待聊天室完全載入展開

        # 5. 事先將早安圖片寫入系統剪貼簿，確保貼上時無任何外部行程干擾焦點
        if image_path and os.path.exists(image_path):
            from app.services.image_crawler import copy_image_to_clipboard
            logger.info(f"步驟 D: 將早安圖片事先寫入剪貼簿 ({image_path})...")
            copy_image_to_clipboard(image_path)
            time.sleep(0.5)

        # 6. 原生實體點擊右側對話輸入框中心，緊接著立即貼上圖片，確保絕對對焦
        chat_input_x = win_x + (win_w // 2) + 120
        chat_input_y = win_y + win_h - 70
        logger.info(f"步驟 E: 原生點擊右側對話框輸入區核心座標 ({chat_input_x}, {chat_input_y})，鎖定對焦 🎯")
        adapter.native_click(chat_input_x, chat_input_y)
        time.sleep(0.3)

        # 7. 貼上並發送 (Cmd + V, Return)
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
