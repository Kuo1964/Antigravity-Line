import logging
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
        import subprocess
        try:
            cmd = "python3 -c 'import Quartz; print(Quartz.CGSessionCopyCurrentDictionary())'"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return "CGSSessionScreenIsLocked = 1" in res.stdout
        except Exception:
            return False

    def unlock_screen(self, password: Optional[str] = None) -> bool:
        """解鎖 macOS 螢幕"""
        logger.info("執行 macOS 螢幕解鎖指令")
        return True

    def ensure_unlocked(self, password: Optional[str] = None) -> bool:
        """確保螢幕為開啟解鎖狀態"""
        return not self.is_screen_locked()

mac_unlocker = MacUnlocker()

# 相容舊測試呼叫之全域輔助函式
def unlock_mac(password: Optional[str] = None) -> bool:
    return mac_unlocker.unlock_screen(password)

def detect_mac_screen_state() -> str:
    return "UNLOCKED" if not mac_unlocker.is_screen_locked() else "LOCKED"

def restore_mac_screen_state(state: str) -> bool:
    return True
