import pytest
import asyncio
import os
from unittest.mock import patch, MagicMock
from app.services.agent_session_engine import agent_session_engine, AgentSessionEngine
from app.services import session_store
from app.config import settings

def test_agent_session_engine_lifecycle():
    """測試 AgentSessionEngine 核心 Session 建立、查詢與重置（含 SessionStore 驗證）」"""
    user_id = "U_ENGINE_TEST_USER_LIFECYCLE"
    agent_session_engine.reset_session(user_id)

    session = agent_session_engine.get_or_create_session(user_id)
    assert "history" in session
    assert agent_session_engine.is_busy(user_id) is False

    # 測試重置
    reset_success = agent_session_engine.reset_session(user_id)
    assert reset_success is True
    assert user_id not in agent_session_engine.sessions
    assert session_store.load_session(user_id) == {}

def test_state_lock_mode(tmp_path):
    """測試 1: 狀態鎖定模式 (State Lock Mode)"""
    user_id = "U_TEST_STATE_LOCK"
    test_session_file = str(tmp_path / "sessions.json")
    
    with patch("app.services.session_store.DEFAULT_SESSION_PATH", test_session_file):
        agent_session_engine.reset_session(user_id)

        project_info = {
            "name": "Antigravity-Line",
            "path": "/fake/path/Antigravity-Line",
            "is_valid_project": True
        }

        # 呼叫 set_user_project 進行狀態鎖定
        agent_session_engine.set_user_project(user_id, project_info)

        # 驗證內存狀態
        session = agent_session_engine.get_or_create_session(user_id)
        assert session.get("is_project_locked") is True
        assert session.get("current_project") == project_info
        assert agent_session_engine.get_user_project(user_id) == project_info

        # 驗證持久化檔案資料
        saved_data = session_store.load_session(user_id, filepath=test_session_file)
        assert saved_data.get("is_project_locked") is True
        assert saved_data.get("current_project") == project_info

        agent_session_engine.reset_session(user_id)

def test_semantic_thought_mode():
    """測試 2: 語意思考模式 (Semantic Thought Mode) 動態切換與鎖定隔離」"""
    user_id = "U_TEST_SEMANTIC_THOUGHT"
    agent_session_engine.reset_session(user_id)

    # Mock project_manager 的 detect_project_from_prompt 與 get_project_file_context
    mock_detected_proj = {"name": "Project-Alpha", "path": "/fake/path/Project-Alpha"}
    
    with patch("app.project_manager.project_manager.detect_project_from_prompt") as mock_detect, \
         patch("app.project_manager.project_manager.get_project_file_context") as mock_get_context:
        
        mock_detect.return_value = mock_detected_proj
        mock_get_context.return_value = "專案名稱: Project-Alpha\n[專案檔案 'README.md' 內容]\nAlpha Context"

        # 情況 A: 未鎖定狀態，提及 Project-Alpha Prompt -> 自動觸發語意思考動態切換
        prompt = "請幫我分析 Project-Alpha 的架構"
        augmented_prompt = agent_session_engine._inject_workspace_context(user_id, prompt)

        mock_detect.assert_called_with(prompt)
        assert "[專案工作區脈絡資訊]" in augmented_prompt
        assert "Alpha Context" in augmented_prompt

        # 情況 B: 狀態鎖定狀態 (鎖定 Project-Beta)，即使 Prompt 提及 Project-Alpha 仍優先使用鎖定專案
        locked_proj = {"name": "Project-Beta", "path": "/fake/path/Project-Beta"}
        agent_session_engine.set_user_project(user_id, locked_proj)
        
        mock_detect.reset_mock()
        mock_get_context.return_value = "專案名稱: Project-Beta\n[專案檔案 'README.md' 內容]\nBeta Context"
        
        augmented_prompt_locked = agent_session_engine._inject_workspace_context(user_id, prompt)
        # 狀態鎖定模式不應呼叫 detect_project_from_prompt
        mock_detect.assert_not_called()
        assert "Beta Context" in augmented_prompt_locked

    agent_session_engine.reset_session(user_id)

def test_session_restore_from_store(tmp_path):
    """測試 3: 服務啟動或讀取時，自動從 session_store 還原歷史 Session 與 current_project"""
    user_id = "U_TEST_RESTORE_USER"
    test_session_file = str(tmp_path / "sessions_restore.json")

    pre_existing_data = {
        "history": [{"user": "Hello", "agent": "Hi there!"}],
        "created_at": 1700000000.0,
        "current_project": {"name": "Restored-Project", "path": "/fake/path/Restored-Project"},
        "is_project_locked": True
    }

    # 模擬直接寫入 SessionStore 檔案
    session_store.save_session(user_id, pre_existing_data, filepath=test_session_file)

    # 建立全新的引擎實例 (模擬重啟)
    new_engine = AgentSessionEngine()

    with patch("app.services.session_store.DEFAULT_SESSION_PATH", test_session_file):
        restored_session = new_engine.get_or_create_session(user_id)

        assert restored_session["history"] == pre_existing_data["history"]
        assert restored_session["current_project"] == pre_existing_data["current_project"]
        assert new_engine.get_user_project(user_id) == pre_existing_data["current_project"]

def test_agent_session_engine_turn_processing():
    """測試 AgentSessionEngine 對話處理與對話歷史寫入持久化」"""
    user_id = "U_ENGINE_TEST_USER_2"
    agent_session_engine.reset_session(user_id)
    settings.GEMINI_API_KEY = "test_mock_key"

    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "這是 Mock 產生的 AI 回應"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        result = asyncio.run(agent_session_engine.process_user_turn(user_id, "測試 AgentSessionEngine"))
        assert result == "這是 Mock 產生的 AI 回應"
        
        session = agent_session_engine.get_or_create_session(user_id)
        assert len(session["history"]) == 1
        assert session["history"][0]["user"] == "測試 AgentSessionEngine"
        assert session["history"][0]["agent"] == "這是 Mock 產生的 AI 回應"

    agent_session_engine.reset_session(user_id)

def test_high_risk_intent_and_confirmation_flow():
    """測試 TICKET-004: 高風險指令意圖判斷、凍結佇列與 YES/confirm 解凍續行機制」"""
    user_id = "U_HIGH_RISK_TEST_USER"
    agent_session_engine.reset_session(user_id)
    settings.GEMINI_API_KEY = "test_mock_key"

    high_risk_prompt = "請幫我刪除 app/temp.py 檔案並修改原始碼"
    
    # 步驟 1: 發送高風險指令 -> 觸發意圖分類攔截，凍結任務
    freeze_reply = asyncio.run(agent_session_engine.process_user_turn(user_id, high_risk_prompt))
    assert freeze_reply == "⚠️ 此指令包含檔案變更/寫入需求，請回覆『YES』以授權 Antigravity 繼續執行。"
    assert agent_session_engine.pending_confirmations.get(user_id) == high_risk_prompt

    # 步驟 2: 發送 YES / /confirm -> 解凍被掛起的任務並由 Gemini SDK 續行處理
    with patch("google.genai.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "已完成高風險操作：成功刪除與修改檔案"
        mock_client.models.generate_content.return_value = mock_response
        mock_client_cls.return_value = mock_client

        confirm_reply = asyncio.run(agent_session_engine.process_user_turn(user_id, "YES"))
        assert confirm_reply == "已完成高風險操作：成功刪除與修改檔案"
        # 驗證 pending 佇列已被清空
        assert user_id not in agent_session_engine.pending_confirmations
        # 驗證對話歷史紀錄的是解凍後的原高風險任務 prompt
        session = agent_session_engine.get_or_create_session(user_id)
        assert len(session["history"]) == 1
        assert session["history"][0]["user"] == high_risk_prompt
        assert session["history"][0]["agent"] == "已完成高風險操作：成功刪除與修改檔案"

    # 步驟 3: 在沒有待確認任務時發送 /confirm
    no_pending_reply = asyncio.run(agent_session_engine.process_user_turn(user_id, "/confirm"))
    assert no_pending_reply == "目前沒有待確認的高風險任務。"

    # 步驟 4: 測試 reset_session 對 pending_confirmations 的清理
    asyncio.run(agent_session_engine.process_user_turn(user_id, "請覆蓋寫入 config.py"))
    assert user_id in agent_session_engine.pending_confirmations
    agent_session_engine.reset_session(user_id)
    assert user_id not in agent_session_engine.pending_confirmations


