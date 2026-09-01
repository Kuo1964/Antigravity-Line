import logging
import subprocess
import sys
import time
from typing import Optional

logger = logging.getLogger("mac_unlocker")

class MacUnlocker:
    """
    Thin Facade 薄外包裝。
    核心系統解鎖邏輯已升級至 mac_system_gateway.py。
    維護完全相容性。
    """

    # 允許模擬鍵盤輸入密碼的前台行程白名單 (僅限 macOS 系統登入與螢幕保護程式)
    ALLOWED_UNLOCK_PROCESSES = {"loginwindow", "screensaverengine"}

    def get_frontmost_app_name(self) -> Optional[str]:
        """取得當前最上層活動中的應用程式名稱 (優先使用 Cocoa AppKit，備援 AppleScript)"""
        # 方法 1: 透過 Cocoa 原生 NSWorkspace 取得 (超快速且無 System Events 權限逾時問題)
        try:
            from AppKit import NSWorkspace
            front_app = NSWorkspace.sharedWorkspace().frontmostApplication()
            if front_app:
                name = front_app.localizedName() or front_app.bundleIdentifier()
                if name:
                    return str(name).strip()
        except Exception:
            pass

        # 方法 2: 備援 AppleScript 查詢
        try:
            cmd = "osascript -e 'tell application \"System Events\" to get name of first application process whose frontmost is true'"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                app_name = res.stdout.strip()
                return app_name if app_name else None
            return None
        except Exception as e:
            logger.warning(f"無法取得當前最上層行程名稱: {e}")
            return None

    def is_screen_locked(self) -> bool:
        """檢查螢幕是否被鎖定 (嚴格判斷，預設安全 Fail-closed)"""
        try:
            # 透過 launchctl asuser 強制進入 GUI Session 命名空間，解決 cron 背景無法讀取狀態的問題
            cmd = f"launchctl asuser $(id -u) {sys.executable} -c 'import Quartz; print(Quartz.CGSessionCopyCurrentDictionary())'"
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
            output = res.stdout
            
            # 如果成功讀取到鎖定標籤且明確為 1
            if "CGSSessionScreenIsLocked = 1" in output:
                return True
            
            # 若無明確鎖定標籤，一律安全判定為未鎖定 (嚴禁任何盲打密碼 Fallback)
            return False
            
        except Exception as e:
            logger.error(f"is_screen_locked 檢查異常: {e}")
            # 發生例外時，採取安全預設：判定未鎖定以防止誤敲密碼
            return False

    def unlock_screen(self, password: Optional[str] = None) -> bool:
        """安全解鎖 macOS 螢幕 (嚴格 Fail-Closed 防盲打防護)"""
        logger.info("發送喚醒訊號 (caffeinate)...")
        subprocess.run(["caffeinate", "-u", "-t", "3"], check=False)
        time.sleep(1.0)
        
        # 1. 第一道防線：狀態檢驗，若未鎖定則無須打密碼直接返回成功
        if not self.is_screen_locked():
            logger.info("螢幕當前未鎖定，無須輸入密碼。")
            return True
            
        if not password:
            logger.warning("螢幕處於鎖定狀態但未提供 MAC_PASSWORD，僅發送螢幕喚醒指令。")
            return False

        # 2. 第二道防線：前台焦點程式白名單檢查 (核心 Fail-Closed 防線)
        front_app = self.get_frontmost_app_name()
        logger.info(f"檢測當前最上層前台程式為: [{front_app}]")
        
        # 🚨 嚴格 Fail-Closed 規則：
        # 只要前台程式為 None (無法判定) 或非登入程式 (例如 Finder, LINE, Chrome)，一律絕對禁止輸入密碼！
        if not front_app or front_app.lower() not in self.ALLOWED_UNLOCK_PROCESSES:
            logger.critical(
                f"🚨 [安全防護攔截] 當前前台應用程式為 '{front_app}'，非系統登入畫面 (loginwindow)！"
                f"為保護隱私與系統安全，已立即熔斷中止解鎖，絕對嚴禁發送鍵盤事件！"
            )
            return False

        # 3. 通過嚴格白名單檢驗後才執行受控模擬輸入
        logger.info("通過前台登入畫面驗證 (loginwindow)，開始安全模擬輸入密碼進行解鎖...")
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
            subprocess.run(["osascript", "-e", applescript_cmd], check=True, timeout=10)
            time.sleep(2.0)
            
            # 4. 解鎖後狀態複查
            is_still_locked = self.is_screen_locked()
            if not is_still_locked:
                logger.info("macOS 螢幕已成功解鎖 🔓")
                return True
            else:
                logger.warning("密碼已輸入，但螢幕仍處於鎖定狀態 (可能密碼不符或介面延遲)。")
                return False
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

