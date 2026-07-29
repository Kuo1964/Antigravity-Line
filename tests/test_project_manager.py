import os
import pytest
from unittest.mock import patch, MagicMock
from app.project_manager import ProjectManager, project_manager
from app.agent_manager import AntigravityAgentManager

def test_project_manager_list_projects(tmp_path):
    """測試 ProjectManager 自動掃描專案資料夾功能"""
    # 在臨時工作區建立假專案
    proj_a = tmp_path / "Project-Alpha"
    proj_a.mkdir()
    (proj_a / "requirements.txt").write_text("fastapi")

    proj_b = tmp_path / "Project-Beta"
    proj_b.mkdir()
    (proj_b / "package.json").write_text("{}")

    pm = ProjectManager(workspace_root=str(tmp_path))
    projects = pm.list_projects()

    assert len(projects) == 2
    names = [p["name"] for p in projects]
    assert "Project-Alpha" in names
    assert "Project-Beta" in names

def test_detect_project_from_prompt(tmp_path):
    """測試從使用者對話中動態解析目標專案"""
    proj_dir = tmp_path / "Antigravity-Line"
    proj_dir.mkdir()
    (proj_dir / ".git").mkdir()

    pm = ProjectManager(workspace_root=str(tmp_path))
    
    # 測試對話精準與模糊匹配
    detected = pm.detect_project_from_prompt("請幫我在 Antigravity-Line 專案跑單元測試")
    assert detected is not None
    assert detected["name"] == "Antigravity-Line"

    detected_short = pm.detect_project_from_prompt("Check line status")
    assert detected_short is not None
    assert detected_short["name"] == "Antigravity-Line"

    detected_none = pm.detect_project_from_prompt("請告訴我今天早上的頭條新聞")
    assert detected_none is None

@pytest.mark.anyio
async def test_agent_manager_project_context():
    """測試 Agent Manager 是否會將專案 Context 動態注入提示詞"""
    manager = AntigravityAgentManager()
    user_id = "test_project_user"

    fake_proj = {"name": "DemoProject", "path": "/path/to/DemoProject"}
    manager.set_user_project(user_id, fake_proj)

    session = manager.get_or_create_session(user_id)
    assert session["current_project"] == fake_proj

    mock_response = MagicMock()
    mock_response.text = "已接收至 DemoProject 指令"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    with patch("app.config.settings.GEMINI_API_KEY", "valid_key"), \
         patch("google.genai.Client", return_value=mock_client):

        result = await manager.run_agent_task(user_id, "執行建置腳本")

        assert "DemoProject" in result
        call_prompt = mock_client.models.generate_content.call_args.kwargs["contents"]
        assert "[當前操作專案Context]" in call_prompt
        assert "DemoProject" in call_prompt
