import asyncio
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app, user_locks
from app.config import settings
from app.agent_manager import agent_manager
from app.services.line_delivery_adapter import line_delivery_adapter

client = TestClient(app)

def setup_function(function):
    """每個測試案例執行前重置白名單與清理 Lock 狀態"""
    settings.ALLOWED_USER_IDS = "U_ALLOWED_TEST_USER"
    user_locks.clear()

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

def test_three_stage_async_push():
    """測試三段式異步推播與進度心跳流程"""
    user_id = "U_ALLOWED_TEST_USER"
    pushed_messages = []

    def mock_deliver_text(uid, text):
        pushed_messages.append((uid, text))
        return True

    async def mock_run_agent_task(uid, prompt):
        # 模擬 Agent 耗時任務，中間會讓出協程觸發心跳
        await asyncio.sleep(0.05)
        return "這是 Agent 最終執行成果"

    original_sleep = asyncio.sleep
    async def fast_sleep(seconds):
        if seconds == 15:
            await original_sleep(0.01)
        else:
            await original_sleep(seconds)

    with patch.object(line_delivery_adapter, "deliver_text", side_effect=mock_deliver_text), \
         patch.object(agent_manager, "run_agent_task", side_effect=mock_run_agent_task), \
         patch("asyncio.sleep", side_effect=fast_sleep):

        payload = {
            "events": [
                {
                    "type": "message",
                    "message": {"type": "text", "text": "請幫我在 Antigravity-Line 跑測試"},
                    "source": {"userId": user_id}
                }
            ]
        }
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        # 第一段推播驗證
        assert len(pushed_messages) >= 1
        assert pushed_messages[0][0] == user_id
        assert "🚀 已成功接收任務，目標專案 [Antigravity-Line]" in pushed_messages[0][1]

        texts = [msg[1] for msg in pushed_messages]
        # 第二段心跳推播驗證
        assert any("⏳ Agent 仍在執行中，請稍候..." in t for t in texts)
        # 第三段成果推播驗證
        assert any("這是 Agent 最終執行成果" in t for t in texts)

def test_user_task_mutex_lock():
    """測試使用者任務互斥鎖 (Lock) 與重複下指令推播提示"""
    user_id = "U_ALLOWED_TEST_USER"
    pushed_messages = []

    def mock_deliver_text(uid, text):
        pushed_messages.append((uid, text))
        return True

    with patch.object(line_delivery_adapter, "deliver_text", side_effect=mock_deliver_text), \
         patch.object(agent_manager, "is_busy", return_value=True):

        payload = {
            "events": [
                {
                    "type": "message",
                    "message": {"type": "text", "text": "執行新任務"},
                    "source": {"userId": user_id}
                }
            ]
        }
        response = client.post("/webhook", json=payload)
        assert response.status_code == 200

        # 驗證推播互斥鎖提示訊息
        assert len(pushed_messages) == 1
        assert pushed_messages[0][1] == "⚠️ 當前已有執行中的任務，請稍候完成後再下達新指令。"
