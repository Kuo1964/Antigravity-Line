import os
import time
import subprocess
import logging

logger = logging.getLogger(__name__)

def is_mac_locked() -> bool:
    """
    檢測 macOS 目前是否處於螢幕鎖定或螢幕保護狀態
    """
    try:
        # 使用 osascript 檢查 System Events 中的 CGSession 狀態
        cmd = [
            "python3",
            "-c",
            "import Quartz; print(Quartz.CGSessionCopyCurrentDictionary())"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if "CGSSessionScreenIsLocked = 1" in res.stdout:
            return True
    except Exception as e:
        logger.warning(f"Quartz 鎖定檢查失敗，嘗試備用方案: {e}")

    # 備用方案：檢查 ScreenSaverEngine 流程或 lockscreen
    try:
        cmd = ["pgrep", "-x", "ScreenSaverEngine"]
        res = subprocess.run(cmd, capture_output=True)
        if res.returncode == 0:
            return True
    except Exception:
        pass

    return False

def wake_mac_screen() -> None:
    """
    喚醒 macOS 螢幕並保持亮屏
    """
    try:
        logger.info("發送喚醒訊號 (caffeinate)...")
        subprocess.run(["caffeinate", "-u", "-t", "3"], check=False)
        time.sleep(1.0)
    except Exception as e:
        logger.error(f"喚醒螢幕時發生錯誤: {e}")

def unlock_mac(password: str) -> bool:
    """
    喚醒並自動解鎖 macOS 螢幕
    :param password: macOS 帳號解鎖密碼
    :return: 是否成功執行解鎖動作
    """
    wake_mac_screen()

    if not password:
        logger.warning("未提供 MAC_PASSWORD，僅發送螢幕喚醒指令。")
        return True

    logger.info("開始模擬輸入密碼進行 macOS 螢幕解鎖...")
    try:
        # AppleScript 模擬按鍵激活輸入框並輸入密碼按下 Enter
        applescript_cmd = f'''
        tell application "System Events"
            key code 123 -- 模擬按左方向鍵喚醒/激活密碼輸入框
            delay 0.5
            keystroke "{password}"
            delay 0.3
            key code 36 -- 按下 Return (Enter) 鍵
        end tell
        '''
        subprocess.run(["osascript", "-e", applescript_cmd], check=True)
        time.sleep(2.0)
        logger.info("macOS 解鎖指令完成發送。")
        return True
    except Exception as e:
        logger.error(f"模擬解鎖密碼失敗: {e}")
        return False
