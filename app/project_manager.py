import os
import logging
from typing import List, Dict, Optional
from app.config import settings

logger = logging.getLogger("project_manager")

class ProjectManager:
    """工作區多專案管理模組，負責自動掃描專案目錄與動態語意識別"""

    def __init__(self, workspace_root: Optional[str] = None):
        self._custom_workspace_root = workspace_root

    @property
    def workspace_root(self) -> str:
        """取得工作區根目錄路徑"""
        return self._custom_workspace_root or settings.effective_workspace_root

    def list_projects(self) -> List[Dict[str, str]]:
        """
        自動掃描工作區總目錄下的所有專案資料夾。
        
        Returns:
            List[Dict[str, str]]: 包含專案名稱 (name) 與絕對路徑 (path) 的列表
        """
        projects = []
        root_path = self.workspace_root

        if not os.path.exists(root_path) or not os.path.isdir(root_path):
            logger.warning(f"工作區根目錄不存在或無效: {root_path}")
            return projects

        try:
            for item in os.listdir(root_path):
                full_path = os.path.join(root_path, item)
                
                # 忽略隱藏資料夾（如 .git, .idea）與非目錄項目
                if item.startswith(".") or not os.path.isdir(full_path):
                    continue

                # 檢查是否具備專案特徵標記檔案
                markers = [".git", "requirements.txt", "package.json", "pyproject.toml", "Dockerfile", "Cargo.toml", "go.mod"]
                is_project = any(os.path.exists(os.path.join(full_path, m)) for m in markers)

                # 若有特徵標記或屬於一般有效資料夾，均納入專案清單
                if is_project or len(os.listdir(full_path)) > 0:
                    projects.append({
                        "name": item,
                        "path": full_path,
                        "is_valid_project": is_project
                    })

        except Exception as e:
            logger.error(f"掃描工作區專案資料夾時發生錯誤: {e}")

        # 依專案名稱排序
        return sorted(projects, key=lambda x: x["name"].lower())

    def detect_project_from_prompt(self, prompt: str) -> Optional[Dict[str, str]]:
        """
        解析使用者 Prompt 中是否提及特定的專案名稱。
        
        Args:
            prompt: 使用者傳入的文字指令
            
        Returns:
            Optional[Dict[str, str]]: 匹配成功的專案資訊，未匹配則回傳 None
        """
        if not prompt:
            return None

        prompt_lower = prompt.lower()
        projects = self.list_projects()

        # 1. 完全或精準比對 (不分大小寫)
        for proj in projects:
            p_name = proj["name"].lower()
            if p_name in prompt_lower or p_name.replace("-", "") in prompt_lower or p_name.replace("_", "") in prompt_lower:
                logger.info(f"從對話中精準匹配到目標專案: {proj['name']} (路徑: {proj['path']})")
                return proj

        # 2. 部分關鍵字或去除符號比對
        for proj in projects:
            # 拆解專案名稱中的關鍵詞 (如 Antigravity-Line -> antigravity, line)
            tokens = [t for t in proj["name"].lower().replace("-", " ").replace("_", " ").split() if len(t) > 3]
            for token in tokens:
                if token in prompt_lower:
                    logger.info(f"從對話中關鍵字匹配到目標專案: {proj['name']} (關鍵字: '{token}')")
                    return proj

        return None

# 全域專案管理單例
project_manager = ProjectManager()
