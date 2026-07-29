import logging
import asyncio
import time
from typing import Dict, Any, Optional
from app.config import settings
from app.project_manager import project_manager

logger = logging.getLogger("agent_manager")

class AntigravityAgentManager:
    """管理使用者與 Antigravity Agent 對話 Session 的核心類別"""

    def __init__(self):
        # 紀錄每個使用者的對話 Session (User ID -> Conversation/History Context)
        self.sessions: Dict[str, Any] = {}
        # 紀錄每個使用者是否正在執行任務
        self.active_tasks: Dict[str, bool] = {}

    def get_or_create_session(self, user_id: str) -> Dict[str, Any]:
        """取得或初始化使用者的對話 Session Context"""
        if user_id not in self.sessions:
            self.sessions[user_id] = {
                "history": [],
                "created_at": time.time(),
                "current_project": None
            }
            logger.info(f"已為使用者 {user_id} 建立新的 Antigravity Agent Session")
        return self.sessions[user_id]

    def reset_session(self, user_id: str) -> bool:
        """重置指定使用者的 Session 對話歷史與目標專案"""
        if user_id in self.sessions:
            del self.sessions[user_id]
            logger.info(f"已重置使用者 {user_id} 的 Session")
            return True
        return False

    def set_user_project(self, user_id: str, project_info: Dict[str, str]):
        """手動或動態設定使用者目前鎖定的目標專案"""
        session = self.get_or_create_session(user_id)
        session["current_project"] = project_info
        logger.info(f"已將使用者 {user_id} 的目標專案切換為: {project_info['name']} ({project_info['path']})")

    def is_busy(self, user_id: str) -> bool:
        """檢查使用者是否有正在執行的 Agent 任務"""
        return self.active_tasks.get(user_id, False)

    async def run_agent_task(self, user_id: str, prompt: str) -> str:
        """
        處理使用者傳送的 Prompt，並透過 Antigravity / Gemini Agent 獲得真實推論與執行結果。
        """
        self.active_tasks[user_id] = True
        session = self.get_or_create_session(user_id)

        try:
            api_key = settings.GEMINI_API_KEY.strip()
            
            # 若未設定 GEMINI_API_KEY 或仍為預設預留字串
            if not api_key or "your_gemini_api_key" in api_key:
                return (
                    "⚠️ [系統提示]\n"
                    "已成功收到您的指令！但目前尚未在 `.env` 中填入有效的 `GEMINI_API_KEY`。\n\n"
                    "請至 Google AI Studio (https://aistudio.google.com/app/api-keys) 免費申請 API Key，"
                    "並貼入 `.env` 的 `GEMINI_API_KEY=` 欄位中，即可啟用真實的智慧 AI 對話與新聞檢索功能！"
                )

            # 動態解析 Prompt 中是否提及特定的專案名稱
            detected_project = project_manager.detect_project_from_prompt(prompt)
            if detected_project:
                self.set_user_project(user_id, detected_project)

            current_project = session.get("current_project")

            # 1. 優先嘗試 Google Antigravity / GenAI SDK 進行推論
            try:
                from google import genai
                from google.genai import types
                client = genai.Client(api_key=api_key)
                
                # 構建帶有專案背景 Context 的 Prompt
                history_text = ""
                for item in session["history"][-5:]:  # 帶入最近 5 輪對話
                    history_text += f"使用者: {item['user']}\nAI: {item['agent']}\n"

                project_context = ""
                file_content_context = ""

                if current_project:
                    proj_name = current_project["name"]
                    proj_path = current_project["path"]
                    project_context = (
                        f"[系統權限宣告]\n"
                        f"您是 Antigravity Agent 控制系統，擁有存取並讀取使用者專案本地檔案與執行指令的完全授權。\n"
                        f"當前鎖定操作專案: {proj_name}\n"
                        f"專案絕對路徑: {proj_path}\n"
                    )

                    # 檢查 Prompt 是否提及特定檔案（例如 SETUP_GUIDE.md, README.md, .env 等），若有則自動前置讀取
                    try:
                        import os
                        if os.path.exists(proj_path):
                            for fname in os.listdir(proj_path):
                                if len(fname) > 3 and fname.lower() in prompt.lower():
                                    file_full_path = os.path.join(proj_path, fname)
                                    if os.path.isfile(file_full_path):
                                        with open(file_full_path, "r", encoding="utf-8", errors="ignore") as f:
                                            content = f.read(8000)
                                            file_content_context += f"\n[專案檔案 '{fname}' 的實際內容]:\n{content}\n"
                                        logger.info(f"已成功前置讀取專案檔案: {fname}")
                    except Exception as fe:
                        logger.warning(f"自動讀取專案檔案時發生警告: {fe}")

                full_prompt = (
                    f"{project_context}"
                    f"{file_content_context}"
                    f"{history_text}"
                    f"使用者: {prompt}\nAI:"
                )
                
                # 若設定檔啟用連網搜尋，配置 Google Search Grounding 工具
                config = None
                if settings.ENABLE_WEB_SEARCH:
                    config = types.GenerateContentConfig(
                        tools=[types.Tool(google_search=types.GoogleSearch())]
                    )
                
                # 使用 Gemini 2.5 Flash / Gemini 2.0 Flash 模型進行即時檢索與推論
                response = client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=full_prompt,
                    config=config
                )
                
                reply_text = response.text.strip()
                session["history"].append({"user": prompt, "agent": reply_text})
                return reply_text
                
            except Exception as genai_err:
                logger.warning(f"google-genai 調用失敗 ({genai_err})，嘗試備用 API 機制...")
                
                # 備用機制：嘗試 google.generativeai
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=api_key)
                model = legacy_genai.GenerativeModel('gemini-1.5-flash')
                response = await asyncio.to_thread(model.generate_content, prompt)
                
                reply_text = response.text.strip()
                session["history"].append({"user": prompt, "agent": reply_text})
                return reply_text

        except Exception as err:
            logger.error(f"Agent 推論過程發生錯誤: {err}")
            return f"❌ Agent 處理任務時發生錯誤：{str(err)}"
        finally:
            self.active_tasks[user_id] = False

# 全域 Agent 管理單例
agent_manager = AntigravityAgentManager()
