import logging
from typing import Dict, Any
from app.services.agent_session_engine import agent_session_engine

logger = logging.getLogger("agent_manager")

class AntigravityAgentManager:
    """
    薄外包裝 (Thin Facade)。
    核心業務邏輯已重構升級至 app/services/agent_session_engine.py 的 AgentSessionEngine 深層模組。
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

    async def run_agent_task(self, user_id: str, prompt: str) -> str:
        """轉向呼叫 AgentSessionEngine 的深層公開主介面"""
        return await agent_session_engine.process_user_turn(user_id, prompt)

# 全域單例維持向下相容
agent_manager = AntigravityAgentManager()
