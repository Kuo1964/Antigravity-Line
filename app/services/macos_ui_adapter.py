import time
import logging
import subprocess
import re
import ctypes
import appscript

logger = logging.getLogger(__name__)

class MacOSUIAdapter:
    """
    Adapter for macOS UI automation.
    Encapsulates AppleScript execution, C-types CoreGraphics interactions,
    and appscript UI events to provide a clean deep interface for controllers.
    """
    
    def __init__(self):
        self._init_core_graphics()
        try:
            self.se = appscript.app("System Events")
        except Exception:
            self.se = None
        self._screen_state = "ON"
        
    def _init_core_graphics(self):
        try:
            self.core_graphics = ctypes.CDLL("/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics")
            self.core_foundation = ctypes.CDLL("/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation")
            
            self.kCGEventLeftMouseDown = 1
            self.kCGEventLeftMouseUp = 2
            self.kCGHIDEventTap = 0

            class CGPoint(ctypes.Structure):
                _fields_ = [("x", ctypes.c_double), ("y", ctypes.c_double)]
            self.CGPoint = CGPoint

            self.core_graphics.CGEventCreateMouseEvent.restype = ctypes.c_void_p
            self.core_graphics.CGEventCreateMouseEvent.argtypes = [ctypes.c_void_p, ctypes.c_uint32, self.CGPoint, ctypes.c_uint32]
            self.core_graphics.CGEventPost.argtypes = [ctypes.c_uint32, ctypes.c_void_p]
            self.core_foundation.CFRelease.argtypes = [ctypes.c_void_p]
            
            self.cg_available = True
        except Exception as e:
            logger.error(f"初始化 CoreGraphics ctypes 失敗: {e}")
            self.cg_available = False

    def save_screen_state(self) -> str:
        """保存當前螢幕狀態"""
        self._screen_state = "ON"
        return self._screen_state

    def restore_screen_state(self) -> bool:
        """復原之前的螢幕狀態"""
        logger.info(f"復原 macOS 螢幕狀態至 {self._screen_state}")
        return True

    def native_click(self, x: int, y: int) -> None:
        """使用 CoreGraphics 原生發送實體點擊"""
        if not self.cg_available:
            logger.error(f"無法發送點擊，CoreGraphics 不可用: ({x}, {y})")
            return
            
        pt = self.CGPoint(float(x), float(y))
        down_event = self.core_graphics.CGEventCreateMouseEvent(None, self.kCGEventLeftMouseDown, pt, 0)
        up_event = self.core_graphics.CGEventCreateMouseEvent(None, self.kCGEventLeftMouseUp, pt, 0)
        
        self.core_graphics.CGEventPost(self.kCGHIDEventTap, down_event)
        self.core_graphics.CGEventPost(self.kCGHIDEventTap, up_event)

        if down_event:
            self.core_foundation.CFRelease(down_event)
        if up_event:
            self.core_foundation.CFRelease(up_event)

    def execute_applescript(self, script: str) -> subprocess.CompletedProcess:
        """執行一段 AppleScript 並回傳結果"""
        return subprocess.run(["osascript", "-e", script], capture_output=True, text=True)

    def reopen_app(self, app_name: str) -> None:
        """使用 AppleScript 的 reopen 指令，喚起應用程式主視窗 (等同點擊 Dock)"""
        script = f'''
        tell application "{app_name}"
            activate
            reopen
        end tell
        '''
        self.execute_applescript(script)
        time.sleep(1.5)

    def unhide_window(self, app_name: str) -> None:
        """確保該應用程式的 Window 1 不是隱藏狀態"""
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                if exists (window 1) then
                    set value of attribute "AXHidden" to false
                end if
            end tell
        end tell
        '''
        self.execute_applescript(script)
        time.sleep(0.5)

    def get_window_bounds(self, app_name: str, retries: int = 10, delay: float = 1.0) -> tuple[int, int, int, int]:
        """取得目標應用程式主視窗的絕對座標與尺寸 (內建重試機制)"""
        script = f'''
        tell application "System Events"
            tell process "{app_name}"
                set winPos to position of window 1
                set winSize to size of window 1
                return (item 1 of winPos as string) & "," & (item 2 of winPos as string) & "," & (item 1 of winSize as string) & "," & (item 2 of winSize as string)
            end tell
        end tell
        '''
        for attempt in range(1, retries + 1):
            try:
                res = self.execute_applescript(script)
                if res.returncode == 0 and res.stdout.strip():
                    numbers = re.findall(r'-?\d+', res.stdout)
                    if len(numbers) >= 4:
                        x, y, w, h = int(numbers[0]), int(numbers[1]), int(numbers[2]), int(numbers[3])
                        logger.info(f"成功獲取 {app_name} 視窗座標: x={x}, y={y}, w={w}, h={h} (嘗試次數: {attempt})")
                        return x, y, w, h
                else:
                    logger.warning(f"取得 {app_name} 視窗座標失敗 (嘗試 {attempt}/{retries})，AppleScript 回傳: {res.stderr.strip()}")
            except Exception as e:
                logger.warning(f"執行 AppleScript 發生異常 (嘗試 {attempt}/{retries}): {e}")
            
            if attempt < retries:
                time.sleep(delay)
                
        logger.error(f"無法取得真實的 {app_name} 視窗座標！")
        return None

    def send_keystroke(self, text: str, using_cmd: bool = False) -> None:
        """模擬鍵盤輸入字串"""
        if not self.se:
            return
        if using_cmd:
            self.se.keystroke(text, using=appscript.k.command_down)
        else:
            self.se.keystroke(text)

    def send_keycode(self, keycode: int) -> None:
        """模擬發送 KeyCode"""
        if not self.se:
            return
        self.se.key_code(keycode)

# 全域單例導出
macos_ui_adapter = MacOSUIAdapter()
