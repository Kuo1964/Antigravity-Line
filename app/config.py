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
    HOST: str = "0.0.0.0"
    PORT: int = 8000

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
