#!/usr/bin/env bash
# ==============================================================================
# Antigravity-Line 排程高可用執行器 (Scheduler Resilient Runner)
# 具備 Python 解譯器多重降級備援機制，防止因單一 symlink 損壞而中斷排程
# ==============================================================================

set -e

# 定位專案目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

# 尋找可用的 Python 解譯器
PYTHON_EXEC=""
if [ -x "$PROJECT_ROOT/venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/venv/bin/python"
elif [ -x "$PROJECT_ROOT/.venv/bin/python" ]; then
    PYTHON_EXEC="$PROJECT_ROOT/.venv/bin/python"
elif [ -x "/opt/homebrew/opt/python@3.12/bin/python3.12" ]; then
    PYTHON_EXEC="/opt/homebrew/opt/python@3.12/bin/python3.12"
elif [ -x "/opt/homebrew/bin/python3" ]; then
    PYTHON_EXEC="/opt/homebrew/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_EXEC="$(command -v python3)"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [CRITICAL] 找不到任何可用的 Python 執行檔！" >&2
    exit 1
fi

export PYTHONPATH="$PROJECT_ROOT"
exec "$PYTHON_EXEC" "$@"
