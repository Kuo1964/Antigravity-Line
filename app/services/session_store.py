"""SessionStore 持久化管理器

負責管理使用者 Session 對話歷史與當前鎖定專案狀態的持久化讀寫。
資料將同步儲存於 app/data/sessions.json。
"""

import json
import os
from threading import Lock
from typing import Dict, Any, Optional

# 預設 Session 檔案儲存路徑
DEFAULT_SESSION_DIR = os.path.join("app", "data")
DEFAULT_SESSION_PATH = os.path.join(DEFAULT_SESSION_DIR, "sessions.json")

# 檔案讀寫互斥鎖，避免多執行緒競爭
_file_lock = Lock()


def _ensure_dir_exists(filepath: str) -> None:
    """確保檔案所在的目錄存在，若不存在則自動建立。

    Args:
        filepath: 檔案路徑
    """
    dirname = os.path.dirname(filepath)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname, exist_ok=True)


def load_all_sessions(filepath: str = DEFAULT_SESSION_PATH) -> Dict[str, Dict[str, Any]]:
    """讀取所有使用者的 Session 資料。

    Args:
        filepath: Session JSON 檔案路徑

    Returns:
        Dict[str, Dict[str, Any]]: 使用者 ID 對應 Session 資料的字典
    """
    with _file_lock:
        if not os.path.exists(filepath):
            return {}
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if not content:
                    return {}
                return json.loads(content)
        except (json.JSONDecodeError, OSError):
            return {}


def load_session(user_id: str, filepath: str = DEFAULT_SESSION_PATH) -> Dict[str, Any]:
    """讀取特定使用者的 Session 資料。

    Args:
        user_id: 使用者 ID
        filepath: Session JSON 檔案路徑

    Returns:
        Dict[str, Any]: 使用者的 Session 資料字典，若無資料則回傳空字典 {}
    """
    sessions = load_all_sessions(filepath=filepath)
    return sessions.get(user_id, {})


def save_session(user_id: str, data: Dict[str, Any], filepath: str = DEFAULT_SESSION_PATH) -> None:
    """寫入或更新特定使用者的 Session 資料至 JSON 檔案。

    Args:
        user_id: 使用者 ID
        data: 使用者 Session 資料（包含對話歷史與鎖定專案狀態等）
        filepath: Session JSON 檔案路徑
    """
    _ensure_dir_exists(filepath)
    with _file_lock:
        sessions = {}
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        sessions = json.loads(content)
            except (json.JSONDecodeError, OSError):
                sessions = {}

        sessions[user_id] = data

        temp_filepath = f"{filepath}.tmp"
        with open(temp_filepath, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        os.replace(temp_filepath, filepath)


def delete_session(user_id: str, filepath: str = DEFAULT_SESSION_PATH) -> bool:
    """刪除特定使用者的 Session 資料。

    Args:
        user_id: 使用者 ID
        filepath: Session JSON 檔案路徑

    Returns:
        bool: 若成功刪除傳回 True，若使用者原本即不存在傳回 False
    """
    _ensure_dir_exists(filepath)
    with _file_lock:
        if not os.path.exists(filepath):
            return False
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                sessions = json.loads(content) if content else {}
        except (json.JSONDecodeError, OSError):
            return False

        if user_id in sessions:
            del sessions[user_id]
            temp_filepath = f"{filepath}.tmp"
            with open(temp_filepath, "w", encoding="utf-8") as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)
            os.replace(temp_filepath, filepath)
            return True
        return False
