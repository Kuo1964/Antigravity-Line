import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
import asyncio
import time

from app.main import app, user_locks
from app.config import settings
from app.agent_manager import agent_manager
from app.services.line_delivery_adapter import line_delivery_adapter

client = TestClient(app)

def test_health_endpoint():
    """測試 /health 端點回傳 status ok"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "Antigravity Line Bot Bridge"}

def test_webhook_no_events():
    """測試當 Line 發送空 events 列表時秒回 HTTP 200 OK」"""
    response = client.post("/webhook", json={"events": []})
    assert response.status_code == 200
    assert response.json() == {"status": "no events"}

def test_webhook_unauthorized_user():
    """測試非授權 Line User ID 存取時被拒絕」"""
    payload = {
        "events": [
            {
                "type": "message",
                "message": {"type": "text", "text": "Hello"},
                "source": {"userId": "U_UNAUTHORIZED_HACKER_ID"}
            }
        ]
    }
    with patch.object(settings, "ALLOWED_USER_IDS", ["U_ALLOWED_TEST_USER"]):
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
        return "這是 Agent 最終執行成果"

    with patch.object(settings, "ALLOWED_USER_IDS", ["U_ALLOWED_TEST_USER"]), \
         patch.object(line_delivery_adapter, "deliver_text", side_effect=mock_deliver_text), \
         patch.object(agent_manager, "run_agent_task", side_effect=mock_run_agent_task):

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

        # 驅動同線程 asyncio 讓背景 Task 完成推播
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.run_until_complete(asyncio.sleep(0.1))
        except Exception:
            asyncio.run(asyncio.sleep(0.1))

        texts = [msg[1] for msg in pushed_messages]
        # 成果推播驗證
        assert any("這是 Agent 最終執行成果" in t for t in texts)

def test_user_task_mutex_lock():
    """測試使用者任務互斥鎖 (Lock) 與重複下指令推播提示"""
    user_id = "U_ALLOWED_TEST_USER"
    pushed_messages = []

    def mock_deliver_text(uid, text):
        pushed_messages.append((uid, text))
        return True

    with patch.object(settings, "ALLOWED_USER_IDS", ["U_ALLOWED_TEST_USER"]), \
         patch.object(line_delivery_adapter, "deliver_text", side_effect=mock_deliver_text), \
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
