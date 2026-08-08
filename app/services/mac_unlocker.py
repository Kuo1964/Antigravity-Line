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

def unlock_mac(password: str = None) -> bool:
    """
    喚醒並解鎖 macOS 螢幕 (含 caffeinate 強效防變黑鎖定保護)
    :param password: Mac 管理員密碼
    :return: 是否成功執行喚醒/解鎖
    """
    pwd = password or os.getenv("MAC_PASSWORD", "")
    logger.info("發送喚醒與強效防變黑鎖定訊號 (caffeinate -d -u -t 60)...")
    try:
        subprocess.Popen(["caffeinate", "-d", "-u", "-t", "60"])
        time.sleep(1.5)
    except Exception as e:
        logger.warning(f"caffeinate 喚醒異常: {e}")

    # 盲打密碼與 Return 鍵解鎖 (針對開機登入畫面與鎖定畫面)
    if pwd:
        logger.info("正在透過 AppleScript 傳送解鎖密碼與 Return 鍵...")
        applescript_cmd = f'''
        with timeout of 10 seconds
            tell application "System Events"
                keystroke "{pwd}"
                delay 0.5
                key code 36
            end tell
        end timeout
        '''
        try:
            subprocess.run(["osascript", "-e", applescript_cmd], capture_output=True, text=True, timeout=12)
            time.sleep(2.0)
            logger.info("已完成密碼與 Return 鍵傳送！")
        except Exception as e:
            logger.warning(f"傳送密碼 AppleScript 異常: {e}")

    return True



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


