import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.agent_manager import agent_manager

client = TestClient(app)

def setup_module(module):
    """測試環境初始化：設定模擬白名單"""
    settings.ALLOWED_USER_IDS = "U_ALLOWED_TEST_USER"

def test_health_check():
    """測試健康檢查端點"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_unauthorized_user_webhook():
    """測試非授權使用者訊息處理"""
    payload = {
        "events": [
            {
                "type": "message",
                "message": {"type": "text", "text": "Hello Agent"},
                "source": {"userId": "U_UNKNOWN_USER"}
            }
        ]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_authorized_user_command_reset():
    """測試授權使用者發送 /reset 指令"""
    user_id = "U_ALLOWED_TEST_USER"
    agent_manager.get_or_create_session(user_id)
    assert user_id in agent_manager.sessions

    payload = {
        "events": [
            {
                "type": "message",
                "message": {"type": "text", "text": "/reset"},
                "source": {"userId": user_id}
            }
        ]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
    # 驗證 session 是否被重置
    assert user_id not in agent_manager.sessions

def test_authorized_user_command_status():
    """測試授權使用者發送 /status 指令"""
    user_id = "U_ALLOWED_TEST_USER"
    payload = {
        "events": [
            {
                "type": "message",
                "message": {"type": "text", "text": "/status"},
                "source": {"userId": user_id}
            }
        ]
    }
    response = client.post("/webhook", json=payload)
    assert response.status_code == 200
