import unittest
from unittest.mock import patch, MagicMock
from app.services.mac_unlocker import MacUnlocker

class TestSafeMacUnlocker(unittest.TestCase):
    def setUp(self):
        self.unlocker = MacUnlocker()

    def test_unlocked_screen_skips_password(self):
        """測試 1：螢幕未鎖定時，直接回傳 True，絕不調用 osascript 敲密碼"""
        with patch.object(self.unlocker, "is_screen_locked", return_value=False), \
             patch("subprocess.run") as mock_run:
            
            result = self.unlocker.unlock_screen(password="MySecretPassword123")
            self.assertTrue(result)
            for call_args in mock_run.call_args_list:
                cmd = call_args[0][0]
                if isinstance(cmd, list):
                    self.assertNotIn("osascript", cmd)
                elif isinstance(cmd, str):
                    self.assertNotIn("osascript", cmd)

    def test_locked_screen_with_forbidden_front_app_blocks_password(self):
        """測試 2：螢幕鎖定但前台程式為 Finder/LINE/Chrome 時，觸發 Fail-Closed 安全防線攔截"""
        forbidden_apps = ["Finder", "LINE", "Google Chrome", "Antigravity", "Terminal"]
        for app in forbidden_apps:
            with patch.object(self.unlocker, "is_screen_locked", return_value=True), \
                 patch.object(self.unlocker, "get_frontmost_app_name", return_value=app), \
                 patch("subprocess.run") as mock_run:
                
                result = self.unlocker.unlock_screen(password="MySecretPassword123")
                self.assertFalse(result, f"前台為 {app} 時未能攔截！")
                for call_args in mock_run.call_args_list:
                    cmd = call_args[0][0]
                    if isinstance(cmd, list):
                        self.assertNotIn("osascript", cmd)
                    elif isinstance(cmd, str):
                        self.assertNotIn("osascript", cmd)

    def test_locked_screen_with_none_front_app_blocks_password(self):
        """測試 3：當前台行程為 None (無法判定或逾時) 時，嚴格 Fail-Closed 阻斷密碼輸入"""
        with patch.object(self.unlocker, "is_screen_locked", return_value=True), \
             patch.object(self.unlocker, "get_frontmost_app_name", return_value=None), \
             patch("subprocess.run") as mock_run:
            
            result = self.unlocker.unlock_screen(password="MySecretPassword123")
            self.assertFalse(result)
            for call_args in mock_run.call_args_list:
                cmd = call_args[0][0]
                if isinstance(cmd, list):
                    self.assertNotIn("osascript", cmd)
                    
    def test_locked_screen_with_loginwindow_allows_unlock(self):
        """測試 4：螢幕鎖定且前台確為 loginwindow 時，才允許受控執行解鎖"""
        with patch.object(self.unlocker, "is_screen_locked", side_effect=[True, False]), \
             patch.object(self.unlocker, "get_frontmost_app_name", return_value="loginwindow"), \
             patch("subprocess.run") as mock_run:
            
            mock_run.return_value = MagicMock(returncode=0)
            result = self.unlocker.unlock_screen(password="MySecretPassword123")
            self.assertTrue(result)

    def test_quartz_failure_fails_safe(self):
        """測試 5：Quartz 檢查異常時採取安全預設 (Fail-closed) 判定未鎖定"""
        with patch("subprocess.run", side_effect=Exception("Quartz error")):
            self.assertFalse(self.unlocker.is_screen_locked())

if __name__ == "__main__":
    unittest.main()
