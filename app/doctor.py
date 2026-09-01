# -*- coding: utf-8 -*-
"""
Antigravity-Line 專案專屬健康診斷器 (Project Doctor)
用於快速一鍵診斷專案運行環境、依賴就緒狀態與外部服務連通性。
"""

import os
import sys
import socket
import subprocess
import urllib.request
import json
from typing import Dict, Any, Tuple

# ANSI 色彩定義
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_status(item: str, passed: bool, message: str = "") -> None:
    """輸出格式化的狀態行"""
    mark = f"{GREEN}[✓ PASS]{RESET}" if passed else f"{RED}[✗ FAIL]{RESET}"
    extra = f" - {message}" if message else ""
    print(f" {mark} {BOLD}{item}{RESET}{extra}")


def check_google_drive() -> Tuple[bool, str]:
    """檢查 Google Drive 雲端硬碟目錄是否可正常存取與寫入"""
    cwd = os.getcwd()
    try:
        test_file = os.path.join(cwd, ".doctor_mount_test")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_file)
        return True, f"工作目錄可讀寫 ({cwd})"
    except Exception as e:
        return False, f"工作目錄讀寫異常: {e}"


def check_port_8000() -> Tuple[bool, str]:
    """檢查本地 8000 端口狀態"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1.0)
    result = sock.connect_ex(("127.0.0.1", 8000))
    sock.close()

    if result == 0:
        # 端口有服務在監聽，嘗試抓取進程
        try:
            out = subprocess.check_output(
                ["lsof", "-i", ":8000", "-sTCP:LISTEN", "-t"], text=True
            ).strip()
            return True, f"端口 8000 正常監聽中 (PID: {out.replace(chr(10), ', ')})"
        except Exception:
            return True, "端口 8000 監聽中"
    else:
        return False, "端口 8000 尚未啟動 (FastAPI 服務未運行)"


def check_ngrok_tunnel() -> Tuple[bool, str]:
    """檢查 ngrok 是否正常提供公開隧道"""
    try:
        req = urllib.request.Request("http://127.0.0.1:4040/api/tunnels")
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            tunnels = data.get("tunnels", [])
            if tunnels:
                public_urls = [t.get("public_url") for t in tunnels if t.get("public_url")]
                return True, f"隧道正常: {', '.join(public_urls)}"
            return False, "ngrok 正在運行但未發現活躍的 Tunnel"
    except Exception:
        return False, "ngrok API 未回應 (ngrok 服務未啟動)"


def check_env_credentials() -> Tuple[bool, str]:
    """檢查 LINE Channel 憑證與環境變數"""
    token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
    secret = os.getenv("LINE_CHANNEL_SECRET")

    # 若環境變數無，嘗試從 .env 檢查
    env_file = os.path.join(os.getcwd(), ".env")
    has_env_file = os.path.exists(env_file)

    if token and secret:
        return True, "LINE Token 與 Secret 已於環境變數就緒"
    elif has_env_file:
        return True, ".env 檔案存在 (請確認已包含金鑰)"
    else:
        return False, "缺少 LINE_CHANNEL_ACCESS_TOKEN 或 .env 設定檔"


def check_morning_message_guard() -> Tuple[bool, str]:
    """防護網檢查：確認早安圖發送模組未受損"""
    core_files = [
        "app/services/line_delivery_adapter.py",
        "app/services/agent_session_engine.py",
    ]
    missing = [f for f in core_files if not os.path.exists(os.path.join(os.getcwd(), f))]
    if not missing:
        return True, "核心服務與發送適配器檔案完整"
    else:
        return False, f"缺少關鍵核心檔案: {', '.join(missing)}"


def run_doctor() -> bool:
    """執行全套診斷並輸出報告"""
    print(f"\n{CYAN}{BOLD}========================================={RESET}")
    print(f"{CYAN}{BOLD}   Antigravity-Line Project Doctor 🩺   {RESET}")
    print(f"{CYAN}{BOLD}========================================={RESET}\n")

    checks = [
        ("Google Drive 磁碟掛載", check_google_drive),
        ("服務端口 8000 狀態", check_port_8000),
        ("ngrok 公開隧道狀態", check_ngrok_tunnel),
        ("LINE 憑證與環境變數", check_env_credentials),
        ("早安圖與核心模組防護", check_morning_message_guard),
    ]

    all_passed = True
    for label, func in checks:
        passed, msg = func()
        print_status(label, passed, msg)
        if not passed and label in ["Google Drive 磁碟掛載", "早安圖與核心模組防護"]:
            all_passed = False

    print(f"\n{CYAN}-----------------------------------------{RESET}")
    if all_passed:
        print(f"{GREEN}{BOLD}✨ 專案核心基礎設施健康！{RESET}\n")
    else:
        print(f"{YELLOW}{BOLD}⚠️ 發現部分項目需留意或啟動。{RESET}\n")

    return all_passed


if __name__ == "__main__":
    success = run_doctor()
    sys.exit(0 if success else 1)
