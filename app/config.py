import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """應用程式設定類別，由環境變數或 .env 檔案自動載入"""
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    ALLOWED_USER_IDS: str = ""  # 逗號分隔的 Line User ID 字串
    GEMINI_API_KEY: str = ""
    ENABLE_WEB_SEARCH: bool = True  # 是否開啟 Google Search Grounding 即時連網搜尋功能
    WORKSPACE_ROOT: str = ""  # 工作區總目錄路徑（若留空則自動使用當前專案父目錄）
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    @property
    def effective_workspace_root(self) -> str:
        """取得有效的工作區總目錄絕對路徑"""
        if self.WORKSPACE_ROOT.strip():
            return os.path.abspath(self.WORKSPACE_ROOT.strip())
        # 預設為當前專案 app 目錄所在之父目錄
        current_project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.dirname(current_project_dir)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def allowed_user_id_list(self) -> List[str]:
        """解析逗號分隔的 Line User ID 列表"""
        if not self.ALLOWED_USER_IDS:
            return []
        return [uid.strip() for uid in self.ALLOWED_USER_IDS.split(",") if uid.strip()]

    def is_user_allowed(self, user_id: str) -> bool:
        """檢查給定的 Line User ID 是否在白名單中"""
        allowed_list = self.allowed_user_id_list
        if not allowed_list:
            # 若未設定白名單，預設不允許任何存取以維護安全性
            return False
        return user_id in allowed_list

settings = Settings()
