#!/usr/bin/env python3
"""Harness² Propose-Probe-Compose 專案配置建置與自動化探針驗證腳本。

本腳本負責：
1. 建置並維護 `.agents/` 目錄下的 8 大可編輯 Harness 元件（System Prompt、Guardrails、Memory、Tool Guidance、Subagents、Skills、Scripts、Plugins）。
2. 執行 Probe（探針驗證）：檢查 8 大元件完整性、macOS 原生框架依賴（Quartz、Vision、AppKit）以及雲端與地端排程目錄的 Git 同步狀態。
3. 產出結構化的 Probe 與 Compose 評估報告。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
LOCAL_CRON_ROOT: Path = Path("/Users/johnkuo/worktemp/Antigravity-Line")
AGENTS_DIR: Path = PROJECT_ROOT / ".agents"

# 定義 8 大元件對應的檔案相對路徑（相對於 .agents 目錄）
COMPONENT_FILES: dict[str, str] = {
    "system_prompt": "system_prompt.md",
    "guardrails": "rules/guardrails.md",
    "memory": "memory.md",
    "tool_guidance": "tool_guidance.md",
    "subagents": "subagents/macos-ui-auditor.md",
    "skills": "skills/line-safe-delivery/SKILL.md",
    "scripts": "scripts/probe_registry.json",
    "plugins": "plugins/pre_delivery_check.json",
}


def build_default_component_contents() -> dict[str, str]:
    """產生 8 大 Harness 元件的標準繁體中文配置內容（結合 Invariant 與 Domain 修改）。"""
    return {
        "system_prompt": """# System Prompt (Antigravity-Line 核心指導方針)

1. **思考優先 (Think Twice, Code Once)**：執行任何修改前，必須先於 Artifacts 或 `implementation_plan.md` 列出導入計畫。
2. **保持最小變更 (Minimal Intervention)**：嚴禁重構與當前任務無關的模組。
3. **不要猜測 (No Guessing)**：遇到模糊需求或缺少的權限/金鑰時，立即停止並詢問使用者。
4. **語言與品質鐵律**：全程思考、對話、文檔與程式碼註解強制使用繁體中文；所有函式必須包含明確 Type Hints，並附帶對應單元測試。
""",
        "guardrails": """# Guardrails (安全防護欄與 Fail-Closed 熔斷規範)

## 1. 預算與工具呼叫控制
- **工具呼叫上限**：單一高階任務連續呼叫工具次數嚴禁超過 8 次。
- **防止死循環**：連續 3 次返回相同錯誤訊息時必須立即中止並回報。

## 2. macOS 螢幕解鎖安全防線
- **白名單強制檢驗**：僅允許在最上層為 `loginwindow` 或 `screensaverengine`（含 Layer >= 1000 遮罩）時模擬鍵盤輸入密碼。
- **黑名單即時熔斷**：若前台為 `LINE`、`Finder`、`Antigravity`、`Terminal` 等一般應用程式，嚴禁輸出任何密碼字元。

## 3. LINE 自動化發送雙重剛性熔斷閘門
- **第一道閘門（搜尋框回讀驗證）**：點擊並輸入目標名稱後，必須回讀 `text field 1 of splitter group 1 of window 1` 的 `value`；若未包含目標名稱，立即觸發 `CRITICAL` 熔斷退出。
- **第二道閘門（Vision OCR 標題視覺核對）**：點擊首筆搜尋結果開啟聊天室後，必須透過 `screencapture -l <wid>` 與 Apple `Vision` 框架辨識視窗文字；若未包含目標好友名稱，立即觸發 `CRITICAL` 熔斷，絕不貼圖與發送。
""",
        "memory": """# Memory (跨工作階段長期記憶索引)

本元件連結至專案根目錄之 [`AGENT_MEMORY.md`](../AGENT_MEMORY.md) 與 [`CONTEXT.md`](../CONTEXT.md)。

## 核心狀態追蹤清單
- **雲端工作目錄**：`/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line`
- **地端排程目錄**：`/Users/johnkuo/worktemp/Antigravity-Line`（系統 Crontab 實際執行路徑）
- **雙端同步鐵律**：任何程式碼與文檔修改完成後，必須 `git commit & push` 並於地端目錄執行 `git pull` 與回歸驗證。
""",
        "tool_guidance": """# Tool Guidance (工具呼叫精準指引)

1. **精準檢索 (Scoped Search)**：禁止在整個專案目錄下無差別搜尋，應先閱讀 `README.md`、`CONTEXT.md` 鎖定目標模組。
2. **禁止盲猜 UI 座標**：操作 macOS 桌面應用程式時，優先透過 Accessibility (`System Events`) 或 `Quartz.CGWindowListCopyWindowInfo` 動態取得真實座標，並泵送 `NSRunLoop` 防止快取停滯。
3. **沙盒與地端同步**：操作地端排程目錄 `/Users/johnkuo/worktemp/Antigravity-Line` 時，應明確申請權限並確認雙端 Git Commit Hash 一致。
""",
        "subagents": """---
name: macos-ui-auditor
description: 專門審查 macOS Accessibility、Quartz 視窗層級與 AppleScript 自動化安全性的子代理。
---

# macOS UI Auditor 子代理規範

當修改涉及 `app/services/mac_unlocker.py`、`app/services/macos_ui_adapter.py` 或 `app/services/line_desktop_controller.py` 時，負責審查：
1. 是否具備 `NSRunLoop` 刷新與 WindowServer 即時查詢機制。
2. 是否維持 Fail-Closed 雙重熔斷（搜尋框回讀 + Vision OCR 標題驗證）。
3. 是否具備完整隔離的單元測試（Mock 系統底層呼叫，不依賴實體螢幕狀態）。
""",
        "skills": """---
name: line-safe-delivery
description: LINE 桌面版早安圖安全解鎖、精準搜尋、雙重熔斷核對與貼圖發送標準技能。
---

# LINE 安全發送標準工作流 (LINE Safe Delivery Skill)

## 標準執行步驟
1. **喚醒與鎖屏判定**：發送 `caffeinate -u -t 3`，透過 `CGSSessionScreenIsLocked` 與 Layer >= 1000 `loginwindow` 判定鎖定狀態。
2. **安全解鎖與輪詢**：通過白名單驗證後輸入密碼，並以最高 8 秒（每 0.5 秒一次）動態輪詢等待登入畫面淡出。
3. **強效置頂 LINE**：呼叫 `open -a LINE`、AppleScript `reopen` 與 `NSApplicationActivateIgnoringOtherApps`，並泵送 `NSRunLoop` 確認置頂。
4. **動態搜尋與回讀驗證**：動態讀取 `text field 1` 座標並點擊中心，貼上目標名稱後回讀 `value` 驗證吻合。
5. **實體點擊首項與 Vision OCR 核對**：實體點擊搜尋框下方首筆結果 `(sf_x + 100, sf_y + sf_h + 60)`，並以 `Vision` OCR 驗證聊天室標題包含目標名稱。
6. **對焦貼圖與發送**：點擊右側輸入框貼上圖片，等待 3.5 秒預覽載入後按 Return 送出（或於 `dry_run=True` 時保留供人工目視檢查）。
""",
        "scripts": json.dumps(
            {
                "probe_script": "scripts/verify_harness_probe.py",
                "simulation_paste_only": "scripts/simulate_paste_only.py",
                "simulation_locked_paste": "scripts/simulate_locked_paste_test.py",
                "doctor": "app/doctor.py",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        "plugins": json.dumps(
            {
                "name": "pre_delivery_verification_hook",
                "version": "1.0.0",
                "description": "在宣告任務完成前強制執行單元測試、探針檢查與雲地端 Git 同步驗證。",
                "hooks": {
                    "pre_complete": [
                        "./venv/bin/pytest tests/test_safe_mac_unlocker_unittest.py tests/test_line_delivery_adapter.py tests/test_harness_probe.py",
                        "./venv/bin/python scripts/verify_harness_probe.py",
                    ]
                },
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    }


def initialize_agents_directory(base_dir: Path = AGENTS_DIR) -> dict[str, str]:
    """初始化並寫入 `.agents/` 目錄下的 8 大元件與 `harness_manifest.json`。"""
    contents = build_default_component_contents()
    created_files: dict[str, str] = {}

    for comp_name, rel_path in COMPONENT_FILES.items():
        file_path = base_dir / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(contents[comp_name], encoding="utf-8")
        created_files[comp_name] = str(file_path.relative_to(base_dir.parent))

    manifest = {
        "framework": "Google Harness² (Recursive Agent Harnessing)",
        "project": "Antigravity-Line",
        "recursion_mode": "Propose-Probe-Compose",
        "components": created_files,
    }
    manifest_path = base_dir / "harness_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return created_files


def probe_components(base_dir: Path = AGENTS_DIR) -> dict[str, bool]:
    """探針 1：檢查 `.agents/` 8 大元件檔案是否存在且非空。"""
    status: dict[str, bool] = {}
    for comp_name, rel_path in COMPONENT_FILES.items():
        target = base_dir / rel_path
        status[comp_name] = target.is_file() and target.stat().st_size > 0
    return status


def probe_macos_frameworks() -> dict[str, bool]:
    """探針 2：檢查目前 Python 環境是否具備 Quartz、AppKit 與 Vision 原生框架。"""
    frameworks: tuple[str, ...] = ("Quartz", "AppKit", "Vision")
    return {
        fw: importlib.util.find_spec(fw) is not None for fw in frameworks
    }


def get_git_head(repo_dir: Path) -> str:
    """取得指定 Git 儲存庫的當前 HEAD Commit Hash。"""
    if not (repo_dir / ".git").exists():
        return "NOT_A_GIT_REPO"
    try:
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(repo_dir),
            capture_output=True,
            text=True,
            check=True,
            timeout=5,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN"


def run_probe_report(base_dir: Path = AGENTS_DIR) -> dict[str, Any]:
    """執行完整專案 Harness² 探針檢查並回傳結構化報告。"""
    comp_status = probe_components(base_dir)
    fw_status = probe_macos_frameworks()
    cloud_head = get_git_head(PROJECT_ROOT)
    local_head = get_git_head(LOCAL_CRON_ROOT) if LOCAL_CRON_ROOT.exists() else "MISSING"

    all_components_ok = all(comp_status.values())
    all_frameworks_ok = all(fw_status.values())

    return {
        "all_components_ready": all_components_ok,
        "component_count": f"{sum(comp_status.values())}/{len(comp_status)}",
        "components": comp_status,
        "all_frameworks_ready": all_frameworks_ok,
        "frameworks": fw_status,
        "git_sync": {
            "cloud_head": cloud_head,
            "local_head": local_head,
            "in_sync": cloud_head == local_head and cloud_head not in ("UNKNOWN", "NOT_A_GIT_REPO"),
        },
    }


def main() -> None:
    """CLI 入口：支援初始化 `.agents` 元件與執行探針檢測。"""
    parser = argparse.ArgumentParser(description="Antigravity-Line Harness² 探針驗證工具")
    parser.add_argument(
        "--init-components",
        action="store_true",
        help="初始化或更新 .agents/ 目錄下的 8 大 Harness 元件配置",
    )
    args = parser.parse_args()

    if args.init_components:
        initialize_agents_directory(AGENTS_DIR)

    report = run_probe_report(AGENTS_DIR)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not (report["all_components_ready"] and report["all_frameworks_ready"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
