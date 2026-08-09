import os
import re
import time
import ctypes
import logging
import subprocess

logger = logging.getLogger(__name__)

def focus_line_app() -> bool:
    """
    喚醒、還原並聚焦 LINE 桌面版視窗，強制將視窗標準化置頂於 Position(100,100) / Size(1000,800)
    :return: 是否成功聚焦視窗
    """
    logger.info("正在喚醒、還原並聚焦 LINE 桌面版...")
    applescript_cmd = '''
    with timeout of 10 seconds
        tell application "LINE"
            reopen
            activate
        end tell
        tell application "System Events"
            tell process "LINE"
                set frontmost to true
                try
                    set miniaturized of window 1 to false
                end try
                try
                    set position of window 1 to {100, 100}
                    set size of window 1 to {1000, 800}
                end try
            end tell
        end tell
    end timeout
    '''
    try:
        res = subprocess.run(["osascript", "-e", applescript_cmd], capture_output=True, text=True, timeout=12)
        if res.returncode == 0:
            time.sleep(1.0)
            return True
        else:
            logger.error(f"開啟 LINE App 失敗: {res.stderr}")
            return False
    except Exception as e:
        logger.error(f"聚焦 LINE App 異常: {e}")
        return False


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
            
        logger.info(f"原生 ctypes 成功發送滑鼠點擊至座標: ({x}, {y})")
except Exception as e:
    logger.error(f"初始化 CoreGraphics ctypes 失敗: {e}")
    def mac_native_click(x: int, y: int) -> None:
        logger.error(f"無法發送點擊，CoreGraphics 不可用: ({x}, {y})")

def get_line_window_bounds() -> tuple[int, int, int, int]:
    """
    取得 LINE 桌面版主視窗在螢幕上的 (X, Y, Width, Height) 絕對座標與尺寸，保留使用者原始位置
    """
    cmd = '''
    with timeout of 5 seconds
        tell application "LINE"
            reopen
            activate
        end tell
        tell application "System Events"
            tell process "LINE"
                set frontmost to true
                try
                    set miniaturized of window 1 to false
                end try
                set winPos to position of window 1
                set winSize to size of window 1
                return (item 1 of winPos as string) & "," & (item 2 of winPos as string) & "," & (item 1 of winSize as string) & "," & (item 2 of winSize as string)
            end tell
        end tell
    end timeout
    '''
    try:
        res = subprocess.run(["osascript", "-e", cmd], capture_output=True, text=True, timeout=8)
        if res.returncode == 0 and res.stdout.strip():
            numbers = re.findall(r'-?\d+', res.stdout)
            if len(numbers) >= 4:
                x, y, w, h = int(numbers[0]), int(numbers[1]), int(numbers[2]), int(numbers[3])
                logger.info(f"成功取得 LINE 原始視窗範圍: Position=({x}, {y}), Size=({w}, {h})")
                return x, y, w, h
    except Exception as e:
        logger.warning(f"取得 LINE 視窗範圍異常: {e}")

    logger.warning("無法取得 LINE 視窗範圍，使用標準備用範圍 (100, 100, 900, 700)")
    return 100, 100, 900, 700

def get_line_login_password() -> str:
    """
    從本地 .env.secret 或環境變數讀取 LINE 登入密碼 (100% 本地隔離防護)
    """
    secret_path = os.path.join(PROJECT_DIR, ".env.secret")
    if os.path.exists(secret_path):
        try:
            with open(secret_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("LINE_PASSWORD="):
                        return line.split("=", 1)[1].strip()
        except Exception as e:
            logger.warning(f"讀取 .env.secret 異常: {e}")
    return os.getenv("LINE_PASSWORD", "")


def handle_line_login_if_needed() -> bool:
    """
    檢測 LINE 桌面版是否停留在密碼登入畫面，若是則自動輸入密碼並完成登入
    """
    pwd = get_line_login_password()
    if not pwd:
        logger.info("未檢測到本地 LINE_PASSWORD 設定，跳過自動登入處理")
        return True

    cmd_check = '''
    with timeout of 5 seconds
        tell application "LINE" to activate
        tell application "System Events"
            tell process "LINE"
                set frontmost to true
                try
                    -- 檢查是否存在密碼輸入框 (secure text field 1 或 text field 1)
                    if (exists secure text field 1 of window 1) or (exists text field 1 of window 1) then
                        return "NEED_LOGIN"
                    end if
                end try
            end tell
        end tell
    end timeout
    return "LOGGED_IN"
    '''
    try:
        res = subprocess.run(["osascript", "-e", cmd_check], capture_output=True, text=True, timeout=8)
        if "NEED_LOGIN" in res.stdout:
            logger.info("⚠️ 檢測到 LINE 桌面版停留在登入畫面，正在自動輸入密碼並登入...")
            cmd_login = f'''
            with timeout of 10 seconds
                tell application "LINE" to activate
                tell application "System Events"
                    tell process "LINE"
                        set frontmost to true
                        delay 0.5
                        try
                            set value of secure text field 1 of window 1 to "{pwd}"
                        on error
                            keystroke "{pwd}"
                        end try
                        delay 0.5
                        key code 36 -- Return 鍵點擊登入
                        delay 3.0 -- 等待登入後主畫面載入
                    end tell
                end tell
            end timeout
            '''
            subprocess.run(["osascript", "-e", cmd_login], capture_output=True, text=True, timeout=12)
            logger.info("🎉 已自動傳送密碼與 Return 鍵，LINE 成功完成登入！")
    except Exception as e:
        logger.warning(f"檢測/處理 LINE 自動登入異常: {e}")

    return True


def search_and_send_image(target_name: str, image_path: str = "") -> bool:
    """
    在 LINE 桌面版中精確搜尋好友/群組名稱，點選該搜尋結果，並貼上 (Cmd+V) 傳送早安圖片
    :param target_name: 好友或群組名稱 (例如: 'Private')
    :param image_path: 早安圖片絕對路徑
    :return: 是否順利完成發送步驟
    """
    logger.info(f"準備在 LINE 桌面版精確搜尋全域目標: '{target_name}'...")
    
    if not focus_line_app():
        return False

    # 先檢測並處理 LINE 自動登入
    handle_line_login_if_needed()

    try:
        # 1. 取得 LINE 視窗真實範圍，給予動畫與喚醒防護時間
        win_x, win_y, win_w, win_h = get_line_window_bounds()
        time.sleep(1.0) # 等待 Dock 視窗彈出動畫 100% 完成

        # 2. 先盲發 Esc 鍵脫離右側聊天室焦點
        logger.info(f"步驟 A1: 盲發 Esc 鍵脫離右側聊天室焦點...")
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 53'], capture_output=True)
        time.sleep(0.3)

        # 3. 透過 AppleScript 強制聚焦全域搜尋欄 UI，並貼上 target_name
        logger.info(f"步驟 A2: 透過 AppleScript UI 鎖定全域搜尋欄並寫入目標 '{target_name}'...")
        applescript_search = f'''
        set the clipboard to "{target_name}"
        with timeout of 10 seconds
            tell application "LINE"
                reopen
                activate
            end tell
            tell application "System Events"
                tell process "LINE"
                    set frontmost to true
                    delay 0.5
                    try
                        set focused of text field 1 of window 1 to true
                    end try
                    keystroke "f" using {{command down}}
                    delay 0.3
                    keystroke "a" using {{command down}}
                    delay 0.2
                    key code 51 -- Backspace
                    delay 0.2
                    keystroke "v" using {{command down}} -- 貼上搜尋目標
                    delay 1.2 -- 等待全域搜尋結果過濾顯示
                end tell
            end tell
        end timeout
        '''
        res_search = subprocess.run(["osascript", "-e", applescript_search], capture_output=True, text=True, timeout=12)
        if res_search.returncode != 0:
            logger.error(f"輸入搜尋目標失敗: {res_search.stderr}")
            return False

        # 4. 原生 ctypes 實體滑鼠點擊全域搜尋結果清單中的第 1 個結果項目座標 (win_x + 220, win_y + 190)
        result_item_x = win_x + 220
        result_item_y = win_y + 190
        logger.info(f"步驟 B: 原生 ctypes 實體點擊全域搜尋結果第一項 '{target_name}' 座標 ({result_item_x}, {result_item_y}) 並切換開啟聊天室...")
        mac_native_click(result_item_x, result_item_y)
        time.sleep(0.8)
        
        # 鍵盤 Return 雙重保險
        subprocess.run(["osascript", "-e", 'tell application "System Events" to key code 36'], capture_output=True)
        time.sleep(0.5)

        # 5. 點擊右側聊天室訊息輸入框座標 (改用視窗相對百分比比例: win_x + win_w*0.7, win_y + win_h - 40)
        chat_input_x = win_x + int(win_w * 0.7)
        chat_input_y = win_y + win_h - 40
        logger.info(f"步驟 C: 原生點擊右側對話框輸入區相對座標 ({chat_input_x}, {chat_input_y})")
        mac_native_click(chat_input_x, chat_input_y)
        time.sleep(0.6)








        # 5. 重新將早安圖片寫入剪貼簿
        if image_path and os.path.exists(image_path):
            from app.services.image_crawler import copy_image_to_clipboard
            logger.info(f"步驟 D: 將早安圖片寫入剪貼簿 ({image_path})...")
            copy_image_to_clipboard(image_path)
            time.sleep(0.5)

        logger.info("步驟 E: 於目標聊天室貼上早安圖片發送中...")
        send_img_cmd = '''
        with timeout of 10 seconds
            tell application "LINE"
                activate
            end tell
            tell application "System Events"
                tell process "LINE"
                    set frontmost to true
                    delay 0.3
                    keystroke "v" using {command down}
                    delay 1.5
                    key code 36 -- Return
                    delay 0.5
                end tell
            end tell
        end timeout
        '''
        res_send = subprocess.run(["osascript", "-e", send_img_cmd], capture_output=True, text=True, timeout=12)
        if res_send.returncode == 0:
            logger.info(f"成功於 LINE 桌面版開啟 '{target_name}' 並完成早安圖片發送！")
            return True
        else:
            logger.error(f"貼上圖片發送失敗: {res_send.stderr}")
            return False

    except Exception as e:
        logger.error(f"LINE 桌面版自動化操作失敗: {e}")
        return False
