import unittest
from app.config import settings
from app.agent_manager import agent_manager

class TestAntigravityLine(unittest.TestCase):

    def setUp(self):
        settings.ALLOWED_USER_IDS = "U_ALLOWED_USER_1,U_ALLOWED_USER_2"

    def test_user_whitelist(self):
        """驗證白名單檢查機制"""
        self.assertTrue(settings.is_user_allowed("U_ALLOWED_USER_1"))
        self.assertTrue(settings.is_user_allowed("U_ALLOWED_USER_2"))
        self.assertFalse(settings.is_user_allowed("U_UNAUTHORIZED_USER"))

    def test_agent_session_management(self):
        """驗證 Session 的建立與重置"""
        user_id = "U_TEST_SESSION_USER"
        session = agent_manager.get_or_create_session(user_id)
        self.assertIn("history", session)

        # 測試重置
        success = agent_manager.reset_session(user_id)
        self.assertTrue(success)
        self.assertNotIn(user_id, agent_manager.sessions)

if __name__ == "__main__":
    unittest.main()
