import logging
import time
import asyncio
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger("agent_session_engine")

class AgentSessionEngine:
    """
    高槓桿、深介面 AgentSessionEngine 模組。
    徹底隱藏專案檔案注入、Search Grounding 工具配置細節與歷史 Context 壓減。
    """

    def __init__(self):
        # 紀錄每個使用者的對話 Session (User ID -> Session Context)
        self.sessions: Dict[str, Any] = {}
        # 紀錄每個使用者是否正在執行任務
        self.active_tasks: Dict[str, bool] = {}

    def get_or_create_session(self, user_id: str) -> Dict[str, Any]:
        """取得或初始化使用者的對話 Session Context"""
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "history": [],
                "created_at": time.time()
            }
            logger.info(f"已為使用者 {user_id} 初始化 AgentSessionEngine 核心 Session")
        return self.sessions[user_id]

    def reset_session(self, user_id: str) -> bool:
        """重置指定使用者的 Session 對話歷史與快取"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"已成功重置使用者 {user_id} 的 Session Context")
            return True
        return False

    def is_busy(self, user_id: str) -> bool:
        """檢查使用者是否有正在執行的 Agent 任務"""
        return self.active_tasks.get(user_id, False)

    def _inject_workspace_context(self, prompt: str) -> str:
        """內部私有方法：自動檢視並注入專案檔案與結構 (Workspace Injector)"""
        try:
            from app.project_manager import project_manager
            # 若包含專案控制關鍵字，自動注入對應工作區檔案結構
            workspace_summary = project_manager.get_active_workspace_summary()
            if workspace_summary:
                return f"[專案工作區脈絡資訊]\n{workspace_summary}\n\n[使用者需求]\n{prompt}"
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
        傳入 user_id 與 prompt，自動處理解析、Gemini Grounding API 配置、推論與 Session 儲存。
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
                    "並貼入 `.env` 的 `GEMINI_API_KEY=` 欄位中！"
                )

            # 自動注入 Workspace 上下文
            augmented_prompt = self._inject_workspace_context(prompt)
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
                return reply_text

            except Exception as genai_err:
                logger.warning(f"Google GenAI SDK 調用失敗 ({genai_err})，嘗試備用處理...")
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=api_key)
                model = legacy_genai.GenerativeModel('gemini-1.5-flash')
                response = await asyncio.to_thread(model.generate_content, full_prompt)
                
                reply_text = response.text.strip()
                session["history"].append({"user": prompt, "agent": reply_text})
                return reply_text

        except Exception as err:
            logger.error(f"AgentSessionEngine 處理過程發生錯誤: {err}")
            return f"❌ Agent 處理任務時發生錯誤：{str(err)}"
        finally:
            self.active_tasks[user_id] = False

# 全域單例
agent_session_engine = AgentSessionEngine()
