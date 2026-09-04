#!/usr/bin/env bash
# 快速執行 Antigravity-Line 健康診斷
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

if [ -f "./venv/bin/python" ]; then
    ./venv/bin/python -m app.doctor
else
    python3 -m app.doctor
fi
