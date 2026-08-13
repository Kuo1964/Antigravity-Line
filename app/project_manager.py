import os
import logging
from typing import List, Dict, Optional, Any
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
        """
        projects = []
        seen_paths = set()

        ignore_dirs = {".git", ".idea", ".vscode", "node_modules", "venv", "__pycache__", "Colab Notebooks", ".DS_Store"}
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
                    seen_paths.add(full_path)
                    projects.append({
                        "name": item,
                        "path": full_path,
                        "is_valid_project": True
                    })

        except Exception as e:
            logger.error(f"掃描專案目錄失敗 ({root}): {e}")

        return sorted(projects, key=lambda x: x["name"].lower())

    def detect_project_from_prompt(self, prompt: str) -> Optional[Dict[str, str]]:
        """解析使用者 Prompt 中是否提及特定的專案名稱"""
        if not prompt:
            return None

        prompt_lower = prompt.lower()
        projects = self.list_projects()

        # 1. 完全或符號去化精準比對
        for proj in projects:
            p_name = proj["name"].lower()
            if p_name in prompt_lower or p_name.replace("-", "") in prompt_lower or p_name.replace("_", "") in prompt_lower:
                logger.info(f"從對話中精準匹配到目標專案: {proj['name']} (路徑: {proj['path']})")
                return proj

        # 2. Token 關鍵字比對
        for proj in projects:
            tokens = [t for t in proj["name"].lower().replace("-", " ").replace("_", " ").split() if len(t) > 3]
            for token in tokens:
                if token in prompt_lower:
                    logger.info(f"從對話中關鍵字匹配到目標專案: {proj['name']} (關鍵字: '{token}')")
                    return proj

        return None

    def get_project_file_context(self, project_info: Dict[str, Any], prompt: str) -> str:
        """根據給定的專案資訊與 Prompt，深度掃描與預載專案中的檔案與文件內容」"""
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

        ignore_dirs = {".git", ".idea", ".vscode", "node_modules", "venv", "__pycache__"}

        try:
            # 遍歷專案目錄 (支援多層子目錄掃描，最高 3 層深度)
            markdown_files = []
            for root, dirs, files in os.walk(proj_path):
                dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith(".")]
                depth = root[len(proj_path):].count(os.sep)
                if depth > 3:
                    continue

                for f in files:
                    if f.startswith("."):
                        continue
                    full_f_path = os.path.join(root, f)
                    rel_f_path = os.path.relpath(full_f_path, proj_path)

                    # 若檔名直接出現在 prompt 中
                    if f in prompt or rel_f_path in prompt:
                        with open(full_f_path, "r", encoding="utf-8", errors="ignore") as fh:
                            content = fh.read(4000)
                            context_lines.append(f"\n[專案檔案 '{rel_f_path}' 的實際內容]\n{content}")

                    if f.endswith(".md") or f.endswith(".json") or f.endswith(".txt"):
                        markdown_files.append((rel_f_path, full_f_path))

            # 如果未透過檔名精確比對成功，且提及行程/規劃/狀態，自動預載 key 文檔 (最多預載 3 個文檔)
            if not any("[專案檔案" in line for line in context_lines) and markdown_files:
                for rel_path, full_path in markdown_files[:3]:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                        content = fh.read(3000)
                        context_lines.append(f"\n[專案檔案 '{rel_path}' 的實際內容]\n{content}")

        except Exception as e:
            logger.warning(f"深度掃描與預載專案檔案內容失敗: {e}")

        return "\n".join(context_lines)

    def get_active_workspace_summary(self) -> str:
        """取得目前工作區整體動態摘要"""
        projects = self.list_projects()
        if not projects:
            return ""
        summary = "已知專案清單:\n"
        for p in projects[:10]:
            summary += f"- {p['name']} (路徑: {p['path']})\n"
        return summary

project_manager = ProjectManager()
