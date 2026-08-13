import logging
import subprocess
import time
from typing import Optional

logger = logging.getLogger("mac_unlocker")

class MacUnlocker:
    """
    Thin Facade 薄外包裝。
    核心系統解鎖邏輯已升級至 mac_system_gateway.py。
    維護完全相容性。
    """

    def is_screen_locked(self) -> bool:
        """檢查螢幕是否被鎖定"""
        try:
            cmd = "python3 -c 'import Quartz; print(Quartz.CGSessionCopyCurrentDictionary())'"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return "CGSSessionScreenIsLocked = 1" in res.stdout
        except Exception:
            return False

    def unlock_screen(self, password: Optional[str] = None) -> bool:
        """解鎖 macOS 螢幕"""
        logger.info("發送喚醒訊號 (caffeinate)...")
        subprocess.run(["caffeinate", "-u", "-t", "3"], check=False)
        time.sleep(1.0)
        
        if not self.is_screen_locked():
            return True
            
        if not password:
            logger.warning("未提供 MAC_PASSWORD，僅發送螢幕喚醒指令。")
            return True

        logger.info("開始模擬輸入密碼進行 macOS 螢幕解鎖...")
        try:
            applescript_cmd = f'''
            tell application "System Events"
                key code 123
                delay 0.5
                keystroke "{password}"
                delay 0.3
                key code 36
            end tell
            '''
            subprocess.run(["osascript", "-e", applescript_cmd], check=True)
            time.sleep(2.0)
            return True
        except Exception as e:
            logger.error(f"模擬解鎖密碼失敗: {e}")
            return False

    def ensure_unlocked(self, password: Optional[str] = None) -> bool:
        """確保螢幕為開啟解鎖狀態"""
        self.unlock_screen(password)
        return not self.is_screen_locked()
        
    def lock_screen(self) -> bool:
        """重新鎖定螢幕"""
        try:
            time.sleep(1.0)
            subprocess.run(["pmset", "displaysleepnow"], check=False)
            logger.info("已成功恢復發送前狀態：Mac 顯示器已重新睡眠並鎖定 🔐")
            return True
        except Exception as e:
            logger.error(f"恢復螢幕睡眠鎖定失敗: {e}")
            return False

mac_unlocker = MacUnlocker()

# 相容舊測試呼叫之全域輔助函式
def unlock_mac(password: Optional[str] = None) -> bool:
    return mac_unlocker.unlock_screen(password)

def detect_mac_screen_state() -> str:
    return "UNLOCKED" if not mac_unlocker.is_screen_locked() else "LOCKED"

def restore_mac_screen_state(state: str) -> bool:
    if state == "LOCKED":
        return mac_unlocker.lock_screen()
    return True

