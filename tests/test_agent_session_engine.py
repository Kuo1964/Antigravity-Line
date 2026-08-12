import pytest
import asyncio
from app.services.agent_session_engine import agent_session_engine
from app.config import settings

def test_agent_session_engine_lifecycle():
    """測試 AgentSessionEngine 核心 Session 建立、查詢與重置」"""
    user_id = "U_ENGINE_TEST_USER"
    session = agent_session_engine.get_or_create_session(user_id)
    assert "history" in session
    assert agent_session_engine.is_busy(user_id) is False

    # 測試重置
    reset_success = agent_session_engine.reset_session(user_id)
    assert reset_success is True
    assert user_id not in agent_session_engine.sessions

def test_agent_session_engine_turn_processing():
    """測試 AgentSessionEngine 對話處理邏輯」"""
    user_id = "U_ENGINE_TEST_USER_2"
    settings.GEMINI_API_KEY = "test_mock_key"
    
    # 測試執行流程
    result = asyncio.run(agent_session_engine.process_user_turn(user_id, "測試 AgentSessionEngine"))
    assert result is not None
    assert len(result) > 0
