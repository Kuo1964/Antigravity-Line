import logging
import time
import os
import asyncio
from typing import Dict, Any, Optional, List
from app.config import settings
from app.services import session_store

logger = logging.getLogger("agent_session_engine")

class AgentSessionEngine:
    """
    高槓桿、深介面 AgentSessionEngine 模組。
    徹底隱藏專案檔案注入、Search Grounding 工具配置細節與歷史 Context 壓減。
    支援雙軌專案綁定（狀態鎖定模式 vs 語意思考模式）與 SessionStore 持久化與還原。
    維護 100% 完整向下相容性。
    """

    def __init__(self):
        # 紀錄每個使用者的對話 Session (User ID -> Session Context)
        self.sessions: Dict[str, Any] = {}
        # 紀錄每個使用者是否正在執行任務
        self.active_tasks: Dict[str, bool] = {}
        # 紀錄每個使用者設定的專案 Context (User ID -> Project Info)
        self.user_projects: Dict[str, Any] = {}

    def get_or_create_session(self, user_id: str) -> Dict[str, Any]:
        """取得或初始化使用者的對話 Session Context，支援從 session_store 自動還原」"""
        if user_id not in self.sessions:
            # 嘗試從 session_store 還原歷史 Session 資料
            stored_session = session_store.load_session(user_id)
            if stored_session and isinstance(stored_session, dict):
                self.sessions[user_id] = stored_session
                # 若歷史 Session 中記錄有當前專案，同步還原內存 user_projects
                if stored_session.get("current_project"):
                    self.user_projects[user_id] = stored_session["current_project"]
                logger.info(f"已成功從 SessionStore 為使用者 {user_id} 還原歷史 Session 與專案綁定 Context")
            else:
                self.sessions[user_id] = {
                    "history": [],
                    "created_at": time.time(),
                    "current_project": self.user_projects.get(user_id),
                    "is_project_locked": False
                }
                logger.info(f"已為使用者 {user_id} 初始化 AgentSessionEngine 核心 Session")
        return self.sessions[user_id]

    def reset_session(self, user_id: str) -> bool:
        """重置指定使用者的 Session 對話歷史與快取，並同步從 SessionStore 刪除」"""
        existed = False
        if user_id in self.sessions:
            del self.sessions[user_id]
            existed = True
        if user_id in self.user_projects:
            del self.user_projects[user_id]
            existed = True

        deleted_from_store = session_store.delete_session(user_id)
        if existed or deleted_from_store:
            logger.info(f"已成功重置使用者 {user_id} 的 Session Context 與持久化紀錄")
            return True
        return False

    def is_busy(self, user_id: str) -> bool:
        """檢查使用者是否有正在執行的 Agent 任務"""
        return self.active_tasks.get(user_id, False)

    def set_user_project(self, user_id: str, project_info: Optional[Dict[str, Any]]) -> None:
        """
        狀態鎖定模式：明確綁定特定專案 Context。
        同步更新內存狀態與持久化 SessionStore。
        """
        if project_info:
            self.user_projects[user_id] = project_info
        else:
            self.user_projects.pop(user_id, None)

        session = self.get_or_create_session(user_id)
        session["current_project"] = project_info
        session["is_project_locked"] = bool(project_info)

        # 寫入 SessionStore
        session_store.save_session(user_id, session)
        logger.info(f"已為使用者 {user_id} 狀態鎖定專案 Context: {project_info.get('name') if project_info else None}")

    def get_user_project(self, user_id: str) -> Optional[Dict[str, Any]]:
        """取得特定使用者的專案內容與路徑 Context"""
        return self.user_projects.get(user_id)

    def _inject_workspace_context(self, user_id: str, prompt: str) -> str:
        """
        內部私有方法：自動檢視並注入專案檔案與結構 (Workspace Injector)。
        支援雙軌專案切換：
        - 狀態鎖定模式：使用者手動鎖定專案時優先固定該專案。
        - 語意思考模式：未鎖定時自動透過 project_manager.detect_project_from_prompt 動態識別切換。
        """
        try:
            from app.project_manager import project_manager

            session = self.get_or_create_session(user_id)
            is_locked = session.get("is_project_locked", False)
            user_proj = self.get_user_project(user_id)

            target_proj = None

            # 1. 狀態鎖定模式：已手動鎖定專案時優先使用
            if is_locked and user_proj:
                target_proj = user_proj
                logger.info(f"狀態鎖定模式：使用已鎖定專案 {target_proj.get('name')}")
            else:
                # 2. 語意思考模式：在未鎖定狀態下自動分析 Prompt 識別專案
                detected_proj = project_manager.detect_project_from_prompt(prompt)
                if detected_proj:
                    target_proj = detected_proj
                    logger.info(f"語意思考模式：動態識別並切換注入專案 {target_proj.get('name')} 脈絡")
                elif user_proj:
                    # 預設相容備選專案
                    target_proj = user_proj

            if target_proj:
                file_context = project_manager.get_project_file_context(target_proj, prompt)
                if file_context:
                    return f"[系統權限宣告]\n[專案工作區脈絡資訊]\n{file_context}\n\n[使用者需求]\n{prompt}"

            workspace_summary = project_manager.get_active_workspace_summary()
            if workspace_summary:
                return f"[系統權限宣告]\n[專案工作區脈絡資訊]\n{workspace_summary}\n\n[使用者需求]\n{prompt}"
        except Exception as e:
            logger.warning(f"注入專案工作區脈絡失敗 (可安全忽略): {e}")
        return prompt

    def _compress_history_if_needed(self, history: List[Dict[str, str]], max_turns: int = 6) -> str:
        """內部私有方法：壓減對話歷史，防止 Context 上限溢出」"""
        if not history:
            return ""
        recent_items = history[-max_turns:]
        formatted = ""
        for item in recent_items:
            formatted += f"使用者: {item.get('user', '')}\nAI: {item.get('agent', '')}\n"
        return formatted

    async def process_user_turn(self, user_id: str, prompt: str) -> str:
        """
        深層公開主介面：極簡單一入口。
        傳入 user_id 與 prompt，自動處理解析、專案脈絡注入、Gemini Grounding API 配置、推論與 Session 儲存。
        """
        self.active_tasks[user_id] = True
        session = self.get_or_create_session(user_id)

        try:
            api_key = settings.GEMINI_API_KEY.strip()

            # 若未設定 GEMINI_API_KEY
            if not api_key or "your_gemini_api_key" in api_key:
                return (
                    "⚠️ [系統提示]\n"
                    "已成功收到您的指令！但目前尚未在 `.env` 中填入有效的 `GEMINI_API_KEY`。\n\n"
                    "請至 Google AI Studio (https://aistudio.google.com/app/api-keys) 免費申請 API Key，"
                    "貼入 `.env` 的 `GEMINI_API_KEY=` 欄位中！"
                )

            # 自動注入 Workspace 上下文與預載檔案內容 (包含雙軌專案切換)
            augmented_prompt = self._inject_workspace_context(user_id, prompt)
            # 自動壓減與讀取歷史紀錄
            history_context = self._compress_history_if_needed(session["history"])

            full_prompt = f"{history_context}使用者: {augmented_prompt}\nAI:" if history_context else augmented_prompt

            # 呼叫 Gemini SDK
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key)

                # 配置 Google Search Grounding 即時連網工具
                config = None
                if settings.ENABLE_WEB_SEARCH:
                    config = types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )

                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_prompt,
                    config=config
                )

                reply_text = response.text.strip()
                session["history"].append({"user": prompt, "agent": reply_text})
                session_store.save_session(user_id, session)
                return reply_text

            except Exception as genai_err:
                logger.warning(f"Google GenAI SDK 調用失敗 ({genai_err})，嘗試備用處理...")
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=api_key)
                model = legacy_genai.GenerativeModel('gemini-1.5-flash')
                response = await asyncio.to_thread(model.generate_content, full_prompt)

                reply_text = response.text.strip()
                session["history"].append({"user": prompt, "agent": reply_text})
                session_store.save_session(user_id, session)
                return reply_text

        except Exception as err:
            logger.error(f"AgentSessionEngine 處理過程發生錯誤: {err}")
            return f"❌ Agent 處理任務時發生錯誤：{str(err)}"
        finally:
            self.active_tasks[user_id] = False

# 全域單例
agent_session_engine = AgentSessionEngine()

