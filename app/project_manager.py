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
        """
        if not prompt:
            return None

        prompt_lower = prompt.lower()
        projects = self.list_projects()

        for proj in projects:
            p_name = proj["name"].lower()
            if p_name in prompt_lower or p_name.replace("-", "") in prompt_lower or p_name.replace("_", "") in prompt_lower:
                logger.info(f"從對話中精準匹配到目標專案: {proj['name']} (路徑: {proj['path']})")
                return proj

        for proj in projects:
            tokens = [t for t in proj["name"].lower().replace("-", " ").replace("_", " ").split() if len(t) > 3]
            for token in tokens:
                if token in prompt_lower:
                    logger.info(f"從對話中關鍵字匹配到目標專案: {proj['name']} (關鍵字: '{token}')")
                    return proj

        return None

    def get_project_file_context(self, project_info: Dict[str, Any], prompt: str) -> str:
        """
        根據給定的專案資訊與 Prompt，自動掃描與預載專案中的檔案內容。
        """
        if not project_info or not isinstance(project_info, dict):
            return ""

        proj_name = project_info.get("name", "")
        proj_path = project_info.get("path", "")

        context_lines = [
            f"專案名稱: {proj_name}",
            f"專案路徑: {proj_path}"
        ]

        if not proj_path or not os.path.exists(proj_path) or not os.path.isdir(proj_path):
            return "\n".join(context_lines)

        try:
            files_in_dir = os.listdir(proj_path)
            # 1. 檢查 Prompt 是否提及特定檔名 (例如 SETUP_GUIDE.md)
            for f in files_in_dir:
                if f in prompt:
                    f_path = os.path.join(proj_path, f)
                    if os.path.isfile(f_path):
                        with open(f_path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read(2000)
                            context_lines.append(f"\n[專案檔案 '{f}' 的實際內容]\n{content}")
                            return "\n".join(context_lines)

            # 2. 如果提及「行程」或未指定檔案，預載專案內的 .md 檔案 (如葡萄牙巴黎行程)
            if "行程" in prompt or "規劃" in prompt or not any("[專案檔案" in line for line in context_lines):
                for f in files_in_dir:
                    if f.endswith(".md"):
                        f_path = os.path.join(proj_path, f)
                        if os.path.isfile(f_path):
                            with open(f_path, "r", encoding="utf-8", errors="ignore") as fh:
                                content = fh.read(2000)
                                context_lines.append(f"\n[專案檔案 '{f}' 的實際內容]\n{content}")
        except Exception as e:
            logger.warning(f"掃描與預載專案檔案內容失敗: {e}")

        return "\n".join(context_lines)

    def get_active_workspace_summary() -> str:
        """取得目前工作區整體動態摘要"""
        projects = self.list_projects()
        if not projects:
            return ""
        summary = "已知專案清單:\n"
        for p in projects[:10]:
            summary += f"- {p['name']} (路徑: {p['path']})\n"
        return summary

# 全域專案管理單例
project_manager = ProjectManager()
