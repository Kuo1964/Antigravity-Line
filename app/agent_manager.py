import logging
from typing import Dict, Any, Optional
from app.services.agent_session_engine import agent_session_engine
from app.project_manager import project_manager

logger = logging.getLogger("agent_manager")

class AntigravityAgentManager:
    """
    薄外包裝 (Thin Facade)。
    核心業務邏輯已重構升級至 app/services/agent_session_engine.py 的 AgentSessionEngine 深層模組。
    對外維護 complete 舊介面相容性。
    """

    @property
    def sessions(self) -> Dict[str, Any]:
        return agent_session_engine.sessions

    @property
    def active_tasks(self) -> Dict[str, bool]:
        return agent_session_engine.active_tasks

    def get_or_create_session(self, user_id: str) -> Dict[str, Any]:
        return agent_session_engine.get_or_create_session(user_id)

    def reset_session(self, user_id: str) -> bool:
        return agent_session_engine.reset_session(user_id)

    def is_busy(self, user_id: str) -> bool:
        return agent_session_engine.is_busy(user_id)

    def set_user_project(self, user_id: str, project_info: Dict[str, Any]) -> None:
        """相容舊介面：代理呼叫 project_manager 設定特定使用者的專案"""
        project_manager.user_projects[user_id] = project_info

    def get_user_project(self, user_id: str) -> Optional[Dict[str, Any]]:
        """相容舊介面：代理呼叫 project_manager 取得特定使用者的專案"""
        return project_manager.user_projects.get(user_id)

    async def run_agent_task(self, user_id: str, prompt: str) -> str:
        """轉向呼叫 AgentSessionEngine 的深層公開主介面"""
        return await agent_session_engine.process_user_turn(user_id, prompt)

# 全域單例維持向下相容
agent_manager = AntigravityAgentManager()
