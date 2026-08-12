import os
import time
import logging
import appscript
import subprocess
import re
import ctypes

logger = logging.getLogger(__name__)

# 載入 macOS 原生 CoreGraphics C 動態庫 (零第三方依賴)
try:
    core_graphics = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
    core_foundation = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
    
    kCGEventLeftMouseDown = 1
    kCGEventLeftMouseUp = 2
    kCGHIDEventTap = 0

    class CGPoint(ctypes.Structure):
        _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]

    core_graphics.CGEventCreateMouseEvent.restype = ctypes.c_void_p
    core_graphics.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, CGPoint, ctypes.c_uint32]
    core_graphics.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
    core_foundation.CFRelease.argtypes = [ctypes.c_void_p]

    def mac_native_click(x: int, y: int) -> None:
        """
        使用 Python ctypes 原生呼叫 macOS CoreGraphics C API 發送真實滑鼠點擊
        """
        pt = CGPoint(float(x), float(y))
        down_event = core_graphics.CGEventCreateMouseEvent(None, kCGEventLeftMouseDown, pt, 0)
        up_event = core_graphics.CGEventCreateMouseEvent(None, kCGEventLeftMouseUp, pt, 0)
        
        core_graphics.CGEventPost(kCGHIDEventTap, down_event)
        core_graphics.CGEventPost(kCGHIDEventTap, up_event)

        if down_event:
            core_foundation.CFRelease(down_event)
        if up_event:
            core_foundation.CFRelease(up_event)
            
except Exception as e:
    logger.error(f"初始化 CoreGraphics ctypes 失敗: {e}")
    def mac_native_click(x: int, y: int) -> None:
        logger.error(f"無法發送點擊，CoreGraphics 不可用: ({x}, {y})")

def get_line_window_bounds(retries: int = 10, delay: float = 1.0) -> tuple[int, int, int, int]:
    """
    取得 LINE 桌面版主視窗在螢幕上的 (X, Y, Width, Height) 絕對座標與尺寸。
    為防止 macOS 解鎖瞬間輔助使用 API 尚未準備好，加入智慧重試機制。
    """
    cmd = '''
    tell application "System Events"
        tell process "LINE"
            set winPos to position of window 1
            set winSize to size of window 1
            return (item 1 of winPos as string) & "," & (item 2 of winPos as string) & "," & (item 1 of winSize as string) & "," & (item 2 of winSize as string)
        end tell
    end tell
    '''
    for attempt in range(1, retries + 1):
        try:
            res = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                numbers = re.findall(r'-?\d+', res.stdout)
                if len(numbers) >= 4:
                    x, y, w, h = int(numbers[0]), int(numbers[1]), int(numbers[2]), int(numbers[3])
                    logger.info(f"成功獲取 LINE 視窗座標: x={x}, y={y}, w={w}, h={h} (嘗試次數: {attempt})")
                    return x, y, w, h
            else:
                logger.warning(f"取得 LINE 視窗座標失敗 (嘗試 {attempt}/{retries})，AppleScript 回傳: {res.stderr.strip()}")
        except Exception as e:
            logger.warning(f"執行 AppleScript 發生異常 (嘗試 {attempt}/{retries}): {e}")
        
        if attempt < retries:
            time.sleep(delay)
            
    logger.error("無法取得真實的 LINE 視窗座標！放棄點擊以避免誤觸。")
    return None

def focus_line_app() -> bool:
    """
    開啟、還原並聚焦 macOS 版 LINE 桌面應用程式
    """
    logger.info("正在喚醒並聚焦 LINE 桌面版...")
    try:
        # 1. 使用原生 AppleScript 的 reopen 指令，模擬點擊 Dock 圖示來喚起主視窗
        cmd_reopen = '''
        tell application "LINE"
            activate
            reopen
        end tell
        '''
        subprocess.run(["osascript", "-e", cmd_reopen], check=False)
        time.sleep(1.5)
        
        # 2. 確保視窗取消隱藏 (輔助保險機制)
        cmd_unhide = '''
        tell application "System Events"
            tell process "LINE"
                if exists (window 1) then
                    set value of attribute "AXHidden" to false
                end if
            end tell
        end tell
        '''
        subprocess.run(["osascript", "-e", cmd_unhide], check=False)
        time.sleep(0.5)
        return True
    except Exception as e:
        logger.error(f"聚焦 LINE App 異常: {e}")
        return False

def search_and_send_image(target_name: str, image_path: str = "") -> bool:
    """
    在 LINE 桌面版中精確搜尋好友/群組名稱，點選該搜尋結果，並貼上 (Cmd+V) 傳送早安圖片
    """
    logger.info(f"準備使用 appscript 與混合控制精確搜尋: '{target_name}'...")
    
    if not focus_line_app():
        return False

    try:
        se = appscript.app("System Events")
        
        # 1. 取得視窗座標並原生點擊全域搜尋框 (避免 Cmd+F 開啟聊天室內搜尋)
        bounds = get_line_window_bounds()
        if not bounds:
            logger.error("因無法獲取 LINE 視窗真實座標，為了安全起見，終止發送任務。")
            return False
        win_x, win_y, win_w, win_h = bounds
        
        search_x = win_x + 190
        search_y = win_y + 95
        logger.info(f"步驟 A: 原生點擊全域搜尋框座標 ({search_x}, {search_y})")
        mac_native_click(search_x, search_y)
        time.sleep(1.0)

        # 2. 清空原本的搜尋內容 (Cmd+A, Backspace) 並輸入目標名稱
        logger.info(f"步驟 B: 輸入目標名稱 '{target_name}'")
        se.keystroke("a", using=appscript.k.command_down)
        time.sleep(0.3)
        se.key_code(51) # Backspace
        time.sleep(0.5)
        se.keystroke(target_name)
        time.sleep(2.0) # 等待搜尋結果浮現

        # 3. 往下點選搜尋結果清單中的第 1 個結果 (朋友)
        # (已在上方取得 win_x, win_y，直接沿用即可)
        result_item_x = win_x + 220
        result_item_y = win_y + 185
        logger.info(f"步驟 C: 原生實體點擊搜尋結果 '{target_name}' 項目座標 ({result_item_x}, {result_item_y})")
        mac_native_click(result_item_x, result_item_y)
        time.sleep(1.5) # 等待右側聊天室畫面載入

        # 4. 點選右側聊天室下方的對話輸入框，確保游標在那裡
        chat_input_x = win_x + (win_w // 2) + 100
        chat_input_y = win_y + win_h - 60
        logger.info(f"步驟 D: 原生點擊右側對話框輸入區座標 ({chat_input_x}, {chat_input_y})")
        mac_native_click(chat_input_x, chat_input_y)
        time.sleep(0.6)

        # 5. 將圖片寫入系統剪貼簿
        if image_path and os.path.exists(image_path):
            from app.services.image_crawler import copy_image_to_clipboard
            logger.info(f"步驟 E: 將早安圖片寫入剪貼簿 ({image_path})...")
            copy_image_to_clipboard(image_path)
            time.sleep(1.0)

        # 6. 貼上並發送 (Cmd + V, Return)
        logger.info("步驟 F: 於目標聊天室貼上早安圖片並發送...")
        se.keystroke("v", using=appscript.k.command_down)
        logger.info("等待 3.5 秒讓 LINE 完整載入圖片預覽...")
        time.sleep(3.5) # 大幅延長等待，解決半截黑屏問題
        se.key_code(36) # Return 發送
        time.sleep(2.0)
        
        logger.info(f"成功於 LINE 桌面版向 '{target_name}' 完成早安圖片發送！")
        return True

    except Exception as e:
        logger.error(f"LINE appscript 操作失敗: {e}")
        return False








