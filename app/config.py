import os
from typing import Optional, List, Any
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    ALLOWED_USER_IDS: Any = ""
    GEMINI_API_KEY: str = ""
    ENABLE_WEB_SEARCH: bool = True
    MAC_PASSWORD: str = ""
    WORKSPACE_ROOT: str = ""
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def effective_workspace_root(self) -> str:
        """取得有效的工作區根目錄，若未設定則自動讀取目前環境」"""
        if self.WORKSPACE_ROOT and os.path.exists(self.WORKSPACE_ROOT):
            return self.WORKSPACE_ROOT
        return os.getcwd()

    @property
    def allowed_user_id_list(self) -> List[str]:
        """解析逗號分隔的 Line User ID 列表，相容 list 或 str」"""
        if not self.ALLOWED_USER_IDS:
            return []
        if isinstance(self.ALLOWED_USER_IDS, list):
            return [str(uid).strip() for uid in self.ALLOWED_USER_IDS if str(uid).strip()]
        return [str(uid).strip() for uid in str(self.ALLOWED_USER_IDS).split(",") if str(uid).strip()]

    def is_user_allowed(self, user_id: str) -> bool:
        """檢查給定的 Line User ID 是否在白名單中"""
        allowed_list = self.allowed_user_id_list
        if not allowed_list:
            # 若未設定白名單，預設不允許任何存取以維護安全性
            return False
        return user_id in allowed_list

settings = Settings()
