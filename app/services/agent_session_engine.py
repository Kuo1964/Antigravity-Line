import os
import asyncio
import logging
from typing import Dict, Any, Optional, List
from app.config import settings
from app.project_manager import project_manager
from app.services.session_store import session_store

logger = logging.getLogger("agent_session_engine")

class AgentSessionEngine:
    """
    高槓桿、深介面 AgentSessionEngine 模組。
    統一管理 Agent Session 上下文壓減、對話歷史紀錄、搜尋 Grounding 工具綁定、
    雙軌專案綁定以及高風險寫入指令二次確認機制 (TICKET-004)。
    """

    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.active_tasks: Dict[str, bool] = {}
        # 紀錄每個使用者設定的專案 Context (User ID -> Project Info)
        self.user_projects: Dict[str, Any] = {}
        # 紀錄被凍結待確認的高風險任務 (User ID -> Pending Prompt)
        self.pending_confirmations: Dict[str, str] = {}

    def get_or_create_session(self, user_id: str) -> Dict[str, Any]:
        """取得或初始化使用者的對話 Session Context，支援從 session_store 自動還原」"""
        if user_id not in self.sessions:
            stored_session = session_store.load_session(user_id)
            if stored_session and isinstance(stored_session, dict) and "history" in stored_session:
                self.sessions[user_id] = stored_session
                logger.info(f"成功從 session_store 還原使用者 {user_id} 之對話與專案 Session")
                if stored_session.get("current_project"):
                    self.user_projects[user_id] = stored_session["current_project"]
            else:
                self.sessions[user_id] = {
                    "user_id": user_id,
                    "history": [],
                    "current_project": None,
                    "is_project_locked": False
                }

        return self.sessions[user_id]

    def set_user_project(self, user_id: str, project_info: Dict[str, Any]):
        """狀態鎖定模式：綁定與設定使用者當前的目標專案」"""
        session = self.get_or_create_session(user_id)
        session["current_project"] = project_info
        session["is_project_locked"] = True
        self.user_projects[user_id] = project_info
        session_store.save_session(user_id, session)
        logger.info(f"已手動為使用者 {user_id} 鎖定目標專案: {project_info.get('name')}")

    def get_user_project(self, user_id: str) -> Optional[Dict[str, Any]]:
        """取得使用者目前鎖定或已存取的專案」"""
        session = self.get_or_create_session(user_id)
        return session.get("current_project") or self.user_projects.get(user_id)

    def is_busy(self, user_id: str) -> bool:
        """檢查使用者當前是否有執行中的 Agent 任務」"""
        return self.active_tasks.get(user_id, False)

    def reset_session(self, user_id: str) -> bool:
        """清除使用者的對話紀錄、專案綁定與持久化資料」"""
        existed = False
        if user_id in self.sessions:
            del self.sessions[user_id]
            existed = True
        if user_id in self.user_projects:
            del self.user_projects[user_id]
            existed = True
        if user_id in self.pending_confirmations:
            del self.pending_confirmations[user_id]
            existed = True

        deleted_from_store = session_store.delete_session(user_id)
        res = existed or deleted_from_store or True
        logger.info(f"重置與清理使用者 {user_id} 的對話歷史與磁碟 Session 檔")
        return res

    def _inject_workspace_context(self, user_id: str, prompt: str) -> str:
        """
        深層公開介面：根據雙軌專案綁定機制自動注入工作區與專案檔案內容。
        1. 狀態鎖定模式：若已手動 /use 鎖定專案，優先注入該專案檔案內容。
        2. 語意思考模式：未鎖定時自動比對對話中的專案名稱，動態載入專案上下文。
        """
        session = self.get_or_create_session(user_id)
        is_locked = session.get("is_project_locked", False)

        target_proj = None
        if is_locked and session.get("current_project"):
            target_proj = session["current_project"]
        else:
            detected = project_manager.detect_project_from_prompt(prompt)
            if detected:
                target_proj = detected
                session["current_project"] = detected
                session_store.save_session(user_id, session)
            else:
                target_proj = session.get("current_project") or self.user_projects.get(user_id)

        system_manifest = "[系統權限宣告] 你是 Antigravity 2.0 高級 Agent，已獲完整存取權限。請用繁體中文以極度精準、專業、清晰的方式解答使用者問題。\n\n"

        if target_proj:
            proj_context = project_manager.get_project_file_context(target_proj, prompt)
            return (
                f"{system_manifest}"
                f"[專案工作區脈絡資訊]\n"
                f"{proj_context}\n\n"
                f"【使用者需求指示】:\n{prompt}"
            )
        else:
            workspace_summary = project_manager.get_active_workspace_summary()
            return (
                f"{system_manifest}"
                f"【工作區整體現況】\n"
                f"{workspace_summary}\n\n"
                f"【使用者需求指示】:\n{prompt}"
            )

    def _compress_history_if_needed(self, history: List[Dict[str, str]], max_turns: int = 5) -> str:
        """深層隱私方法：自動壓縮與格式化歷史對話紀錄」"""
        if not history:
            return ""

        recent_turns = history[-max_turns:]
        formatted = "【對話歷史脈絡】:\n"
        for item in recent_turns:
            formatted += f"使用者: {item.get('user', '')}\nAI: {item.get('agent', '')}\n"
        return formatted

    def _classify_intent(self, prompt: str) -> str:
        """
        輕量級意圖分類器：判斷需求是否屬於 Read-Only 或 Code-Mutation / File-Deletion。
        分析指令是否包含代碼寫入、刪除檔案或修改原始碼等高風險行為。
        """
        high_risk_keywords = [
            "修改", "刪除", "寫入", "覆蓋", "新增檔案", "建立檔案", "更新代碼", "改寫", 
            "刪檔", "重構", "變更原始碼", "刪除檔案", "寫入檔案", "修改程式碼", "更新檔案",
            "delete", "remove", "write", "create file", "modify", "edit", "overwrite", 
            "refactor", "update code", "rm ", "touch "
        ]
        prompt_lower = prompt.lower()
        for kw in high_risk_keywords:
            if kw in prompt_lower:
                return "code_mutation"
        return "read_only"

    async def process_user_turn(self, user_id: str, prompt: str) -> str:
        """
        深層公開主介面：極簡單一入口。
        對外隱藏 Gemini API 呼叫、Search Grounding、對話歷史壓縮、雙軌專案注入，
        包含 Gemini 輕量級意圖分類與高風險二次確認機制 (TICKET-004)。
        """
        self.active_tasks[user_id] = True
        session = self.get_or_create_session(user_id)

        try:
            clean_prompt = prompt.strip().upper()
            target_prompt = prompt

            # 二次確認授權機制：當用戶傳送 YES 或 /confirm 時，自動解凍續行
            if clean_prompt in ["YES", "/CONFIRM"]:
                if user_id in self.pending_confirmations:
                    target_prompt = self.pending_confirmations.pop(user_id)
                    logger.info(f"使用者 {user_id} 已授權續行高風險任務: {target_prompt}")
                else:
                    return "目前沒有待確認的高風險任務。"
            else:
                # 輕量意圖判斷 (Read-Only vs Code-Mutation/File-Deletion)
                intent = self._classify_intent(prompt)
                if intent == "code_mutation":
                    self.pending_confirmations[user_id] = prompt
                    logger.info(f"偵測到高風險任務 (Code-Mutation/File-Deletion)，已凍結使用者 {user_id} 任務至 pending_confirmations 佇列")
                    return "⚠️ 此指令包含檔案變更/寫入需求，請回覆『YES』以授權 Antigravity 繼續執行。"

            api_key = settings.GEMINI_API_KEY.strip()

            # 若未設定 GEMINI_API_KEY
            if not api_key:
                logger.warning("未偵測到有效的 GEMINI_API_KEY，使用系統降級回答。")
                return (
                    "🤖 系統未偵測到 GEMINI_API_KEY，請於主機上的 `.env` 設定 `GEMINI_API_KEY` 以開啓完整 AI Agent 對話能力。"
                )

            # 自動注入 Workspace 上下文與預載檔案內容 (包含雙軌專案切換)
            augmented_prompt = self._inject_workspace_context(user_id, target_prompt)
            # 自動壓減與讀取歷史紀錄
            history_context = self._compress_history_if_needed(session["history"])

            full_prompt = f"{history_context}使用者: {augmented_prompt}\nAI:" if history_context else augmented_prompt

            # 呼叫 Gemini SDK (透過 asyncio.to_thread 確保非阻塞)
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

                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model='gemini-2.5-flash',
                    contents=full_prompt,
                    config=config
                )

                reply_text = response.text.strip()
                session["history"].append({"user": target_prompt, "agent": reply_text})
                session_store.save_session(user_id, session)
                return reply_text

            except Exception as genai_err:
                logger.warning(f"Google GenAI SDK 調用失敗 ({genai_err})，嘗試備用處理...")
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=api_key)
                model = legacy_genai.GenerativeModel('gemini-1.5-flash')
                response = await asyncio.to_thread(model.generate_content, full_prompt)

                reply_text = response.text.strip()
                session["history"].append({"user": target_prompt, "agent": reply_text})
                session_store.save_session(user_id, session)
                return reply_text

        except Exception as err:
            logger.error(f"AgentSessionEngine 處理過程發生錯誤: {err}")
            return f"❌ Agent 處理任務時發生錯誤：{str(err)}"
        finally:
            self.active_tasks[user_id] = False

# 全域單例
agent_session_engine = AgentSessionEngine()
