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
        自動掃描工作區總目錄及其子目錄下的所有專案資料夾。
        採零延遲目錄特徵比對，避免觸發雲端儲存同步掛起。
        
        Returns:
            List[Dict[str, str]]: 包含專案名稱 (name) 與絕對路徑 (path) 的列表
        """
        projects = []
        seen_paths = set()

        ignore_dirs = {".git", ".idea", ".vscode", "node_modules", "venv", "__pycache__", "Colab Notebooks", ".DS_Store"}

        # 主搜尋根目錄：優先使用 WORKSPACE_ROOT (如 我的雲端硬碟)
        root = self.workspace_root or settings.effective_workspace_root

        if not root or not os.path.exists(root) or not os.path.isdir(root):
            return projects

        try:
            for item in os.listdir(root):
                if item.startswith(".") or item in ignore_dirs:
                    continue
                full_path = os.path.abspath(os.path.join(root, item))
                if not os.path.isdir(full_path) or full_path in seen_paths:
                    continue

                # 如果此資料夾是中介分類資料夾 (如 worktemp)，掃描其下層子專案資料夾
                if item.lower() in ["worktemp", "projects", "workspace", "code", "dev"]:
                    try:
                        for sub_item in os.listdir(full_path):
                            if sub_item.startswith(".") or sub_item in ignore_dirs:
                                continue
                            sub_path = os.path.abspath(os.path.join(full_path, sub_item))
                            if os.path.isdir(sub_path) and sub_path not in seen_paths:
                                seen_paths.add(sub_path)
                                projects.append({
                                    "name": sub_item,
                                    "path": sub_path,
                                    "is_valid_project": True
                                })
                    except Exception:
                        pass
                else:
                    # 一般頂層專案資料夾 (如 Yuanta_FCN, TSMC_AI, IBM)
                    seen_paths.add(full_path)
                    projects.append({
                        "name": item,
                        "path": full_path,
                        "is_valid_project": True
                    })

        except Exception as e:
            logger.error(f"掃描專案目錄失敗 ({root}): {e}")

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
