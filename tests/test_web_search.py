import pytest
from unittest.mock import MagicMock, patch
from app.agent_manager import AntigravityAgentManager
from app.config import settings

@pytest.mark.anyio
async def test_agent_web_search_enabled():
    """測試當 ENABLE_WEB_SEARCH 為 True 時，是否正確載入 Google Search 工具"""
    manager = AntigravityAgentManager()
    
    mock_response = MagicMock()
    mock_response.text = "這是測試獲得的即時新聞內容"
    
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    
    with patch("app.config.settings.GEMINI_API_KEY", "valid_test_api_key"), \
         patch("app.config.settings.ENABLE_WEB_SEARCH", True), \
         patch("google.genai.Client", return_value=mock_client):
        
        result = await manager.run_agent_task("test_user_1", "請告訴我三條今天早上的頭條新聞")
        
        assert "即時新聞內容" in result
        mock_client.models.generate_content.assert_called_once()
        
        # 驗證是否有傳遞 config 並且包含 google_search 工具
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert "config" in call_kwargs
        assert call_kwargs["config"] is not None
        assert len(call_kwargs["config"].tools) > 0
        assert call_kwargs["config"].tools[0].google_search is not None

@pytest.mark.anyio
async def test_agent_web_search_disabled():
    """測試當 ENABLE_WEB_SEARCH 為 False 時，不載入 Google Search 工具"""
    manager = AntigravityAgentManager()
    
    mock_response = MagicMock()
    mock_response.text = "一般對話回應內容"
    
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response
    
    with patch("app.config.settings.GEMINI_API_KEY", "valid_test_api_key"), \
         patch("app.config.settings.ENABLE_WEB_SEARCH", False), \
         patch("google.genai.Client", return_value=mock_client):
        
        result = await manager.run_agent_task("test_user_2", "你好")
        
        assert "一般對話" in result
        call_kwargs = mock_client.models.generate_content.call_args.kwargs
        assert call_kwargs.get("config") is None
