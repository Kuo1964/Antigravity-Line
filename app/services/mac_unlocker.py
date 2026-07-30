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

    # 若螢幕當前未鎖定，直接返回，絕不重複發送密碼 keystroke
    if not is_mac_locked():
        logger.info("檢測到 macOS 螢幕未處於鎖定狀態，跳過輸入密碼步驟。")
        return True

    if not password:
        logger.warning("未提供 MAC_PASSWORD，僅發送螢幕喚醒指令。")
        return True

    logger.info("開始模擬輸入密碼進行 macOS 螢幕解鎖...")
    try:
        applescript_cmd = f'''
        with timeout of 5 seconds
            tell application "System Events"
                key code 123 -- 模擬按左方向鍵喚醒/激活密碼輸入框
                delay 0.5
                keystroke "{password}"
                delay 0.3
                key code 36 -- 按下 Return (Enter) 鍵
            end tell
        end timeout
        '''
        subprocess.run(["osascript", "-e", applescript_cmd], check=True, timeout=8)
        time.sleep(1.5)
        logger.info("macOS 解鎖指令完成發送。")
        return True
    except Exception as e:
        logger.error(f"模擬解鎖密碼失敗: {e}")
        return False


def detect_mac_screen_state() -> dict:
    """
    檢測並記錄發送前 macOS 螢幕是否處於鎖定或睡眠狀態
    """
    locked = is_mac_locked()
    logger.info(f"發送前檢測 macOS 螢幕原始狀態: {'[鎖定/睡眠中]' if locked else '[未鎖定使用中]'}")
    return {"was_locked": locked}

def restore_mac_screen_state(state: dict) -> bool:
    """
    任務執行完畢後，將 macOS 螢幕恢復至執行前的原始狀態
    :param state: 執行前 detect_mac_screen_state() 記錄的狀態字典
    """
    was_locked = state.get("was_locked", False)
    
    if was_locked:
        logger.info("檢測到執行前 Mac 處於鎖定/睡眠狀態，開始自動復原鎖定...")
        try:
            time.sleep(1.0)
            subprocess.run(["pmset", "displaysleepnow"], check=False)
            logger.info("已成功恢復發送前狀態：Mac 顯示器已重新睡眠並鎖定 🔐")
            return True
        except Exception as e:
            logger.error(f"恢復螢幕睡眠鎖定失敗: {e}")
            return False
    else:
        logger.info("檢測到執行前 Mac 為未鎖定使用中，保持目前螢幕開啟狀態，不干擾用戶作業 ✨")
        return True


