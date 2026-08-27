import pytest
from unittest.mock import patch, MagicMock
from app.services.mac_unlocker import MacUnlocker

@pytest.fixture
def unlocker():
    return MacUnlocker()

def test_unlocked_screen_skips_password(unlocker):
    """測試案例 1：螢幕未鎖定時，直接回傳 True，絕不調用 osascript 敲密碼"""
    with patch.object(unlocker, "is_screen_locked", return_value=False), \
         patch("subprocess.run") as mock_run:
        
        result = unlocker.unlock_screen(password="MySecretPassword123")
        
        assert result is True
        # 確保除了 caffeinate 以外，絕無調用 osascript
        for call_args in mock_run.call_args_list:
            cmd = call_args[0][0]
            if isinstance(cmd, list):
                assert "osascript" not in cmd
            elif isinstance(cmd, str):
                assert "osascript" not in cmd

def test_locked_screen_with_forbidden_front_app_blocks_password(unlocker):
    """測試案例 2：螢幕處於鎖定狀態，但前台程式為 LINE/Chrome/IDE 時，觸發安全防線攔截"""
    forbidden_apps = ["LINE", "Google Chrome", "Antigravity", "Terminal", "Finder"]
    
    for app in forbidden_apps:
        with patch.object(unlocker, "is_screen_locked", return_value=True), \
             patch.object(unlocker, "get_frontmost_app_name", return_value=app), \
             patch("subprocess.run") as mock_run:
            
            result = unlocker.unlock_screen(password="MySecretPassword123")
            
            # 必須拒絕並回傳 False
            assert result is False, f"在前台為 {app} 時未能攔截密碼輸入！"
            
            # 確保絕無調用 osascript 輸入密碼
            for call_args in mock_run.call_args_list:
                cmd = call_args[0][0]
                if isinstance(cmd, list):
                    assert "osascript" not in cmd
                elif isinstance(cmd, str):
                    assert "osascript" not in cmd

def test_locked_screen_with_loginwindow_allows_unlock(unlocker):
    """測試案例 3：螢幕鎖定且前台確為 loginwindow 時，安全執行解鎖並驗證結果"""
    # 第一次 is_screen_locked 為 True (鎖定)，輸入密碼後第二次為 False (已解鎖)
    with patch.object(unlocker, "is_screen_locked", side_effect=[True, False]), \
         patch.object(unlocker, "get_frontmost_app_name", return_value="loginwindow"), \
         patch("subprocess.run") as mock_run:
        
        mock_run.return_value = MagicMock(returncode=0)
        result = unlocker.unlock_screen(password="MySecretPassword123")
        
        assert result is True
        # 確認有調用 osascript 進行解鎖
        osascript_called = any(
            isinstance(call_args[0][0], list) and "osascript" in call_args[0][0]
            for call_args in mock_run.call_args_list
        )
        assert osascript_called is True

def test_quartz_failure_fails_safe(unlocker):
    """測試案例 4：當 Session 檢查失敗或發生例外時，採取安全預設 (Fail-closed) 判定未鎖定"""
    with patch("subprocess.run", side_effect=Exception("Quartz error")):
        assert unlocker.is_screen_locked() is False

def test_get_frontmost_app_name_success(unlocker):
    """測試案例 5：測試前台程式名稱取得邏輯"""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="loginwindow\n")
        app_name = unlocker.get_frontmost_app_name()
        assert app_name == "loginwindow"
