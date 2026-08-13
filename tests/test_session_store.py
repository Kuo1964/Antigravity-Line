"""SessionStore 持久化管理器單元測試"""

import os
import shutil
import tempfile
import pytest
from typing import Dict, Any

from app.services.session_store import (
    save_session,
    load_session,
    load_all_sessions,
    delete_session,
    DEFAULT_SESSION_PATH,
    DEFAULT_SESSION_DIR,
)


@pytest.fixture
def temp_session_file():
    """提供乾淨的臨時測試目錄與 Session 檔案路徑"""
    temp_dir = tempfile.mkdtemp()
    session_file = os.path.join(temp_dir, "nested", "test_sessions.json")
    yield session_file
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


def test_load_nonexistent_session(temp_session_file: str) -> None:
    """驗證不存在的 Session 檔案或使用者回傳空字典"""
    session_data = load_session("user_123", filepath=temp_session_file)
    assert session_data == {}


def test_save_and_load_session(temp_session_file: str) -> None:
    """驗證保存與讀取使用者 Session 對話歷史與當前鎖定專案狀態"""
    user_id = "user_456"
    mock_data: Dict[str, Any] = {
        "history": [
            {"role": "user", "content": "你好"},
            {"role": "assistant", "content": "您好！有什麼可以協助您？"},
        ],
        "current_project": "Project-Alpha",
        "last_active": "2026-08-13T12:00:00Z",
    }

    save_session(user_id, mock_data, filepath=temp_session_file)

    # 讀取並驗證恢復邏輯
    loaded_data = load_session(user_id, filepath=temp_session_file)
    assert loaded_data == mock_data
    assert loaded_data["current_project"] == "Project-Alpha"
    assert len(loaded_data["history"]) == 2


def test_auto_create_directory(temp_session_file: str) -> None:
    """驗證當目錄不存在時自動建立目錄與檔案"""
    dirname = os.path.dirname(temp_session_file)
    assert not os.path.exists(dirname)

    save_session("user_789", {"current_project": "Project-Beta"}, filepath=temp_session_file)

    assert os.path.exists(dirname)
    assert os.path.exists(temp_session_file)


def test_multi_user_sessions(temp_session_file: str) -> None:
    """驗證多使用者的 Session 保存與獨立性"""
    user1_data = {"current_project": "Project-A", "history": []}
    user2_data = {"current_project": "Project-B", "history": [{"role": "user", "content": "test"}]}

    save_session("user_1", user1_data, filepath=temp_session_file)
    save_session("user_2", user2_data, filepath=temp_session_file)

    all_sessions = load_all_sessions(filepath=temp_session_file)
    assert len(all_sessions) == 2
    assert load_session("user_1", filepath=temp_session_file) == user1_data
    assert load_session("user_2", filepath=temp_session_file) == user2_data


def test_delete_session(temp_session_file: str) -> None:
    """驗證 Session 刪除邏輯"""
    save_session("user_del", {"current_project": "Project-X"}, filepath=temp_session_file)
    assert load_session("user_del", filepath=temp_session_file) != {}

    result = delete_session("user_del", filepath=temp_session_file)
    assert result is True
    assert load_session("user_del", filepath=temp_session_file) == {}

    # 再次刪除不存在的使用者應傳回 False
    result_again = delete_session("user_del", filepath=temp_session_file)
    assert result_again is False


def test_default_session_path_integration() -> None:
    """驗證使用預設路徑 app/data/sessions.json 的自動建檔與讀寫功能"""
    test_user_id = "test_default_user"
    test_payload = {"history": [{"role": "user", "content": "ping"}], "current_project": "DefaultProj"}

    try:
        save_session(test_user_id, test_payload)
        assert os.path.exists(DEFAULT_SESSION_PATH)

        loaded = load_session(test_user_id)
        assert loaded == test_payload
    finally:
        # 清理測試新增的預設 Session
        delete_session(test_user_id)
