import os
import sys
import time
import subprocess
import urllib.request
import json

def daemonize():
    """標準 Unix/macOS 二重 fork (Double-Fork) 系統守護進程化」"""
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as err:
        sys.stderr.write(f"fork #1 失敗: {err}\n")
        sys.exit(1)

    os.chdir("/")
    os.setsid()
    os.umask(0)

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as err:
        sys.stderr.write(f"fork #2 失敗: {err}\n")
        sys.exit(1)

    sys.stdout.flush()
    sys.stderr.flush()
    
    with open(os.devnull, 'r') as f:
        os.dup2(f.fileno(), sys.stdin.fileno())

def main():
    project_dir = "/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
    python_bin = os.path.join(project_dir, "venv", "bin", "python")
    ngrok_bin = "/opt/homebrew/bin/ngrok"

    # 清理舊進程
    subprocess.run(["pkill", "-9", "-f", "uvicorn app.main:app"], stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-f", "ngrok http"], stderr=subprocess.DEVNULL)
    time.sleep(1)

    uvicorn_log = open(os.path.join(project_dir, "uvicorn.log"), "a")
    ngrok_log = open(os.path.join(project_dir, "ngrok.log"), "a")

    # 雙重解耦啟動 FastAPI
    subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=project_dir,
        stdout=uvicorn_log,
        stderr=uvicorn_log,
        start_new_session=True
    )
    time.sleep(2)

    # 雙重解耦啟動 ngrok
    subprocess.Popen(
        [ngrok_bin, "http", "8000", "--log=stdout"],
        cwd=project_dir,
        stdout=ngrok_log,
        stderr=ngrok_log,
        start_new_session=True
    )
    time.sleep(3)

    daemonize()

    # 常駐無限迴圈：保護 uvicorn 與 ngrok 永不死亡
    while True:
        time.sleep(10)

if __name__ == "__main__":
    main()
