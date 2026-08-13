import os
import sys
import time
import subprocess
import urllib.request

def kill_existing():
    subprocess.run(["pkill", "-9", "-f", "uvicorn app.main:app"], stderr=subprocess.DEVNULL)
    subprocess.run(["pkill", "-9", "-f", "ngrok http"], stderr=subprocess.DEVNULL)
    time.sleep(1)

def start_services():
    kill_existing()
    
    project_dir = os.path.dirname(os.path.abspath(__file__))
    python_bin = os.path.join(project_dir, "venv", "bin", "python")
    
    print("🟢 啟動 FastAPI 服務 (Port 8000)...")
    uvicorn_log = open(os.path.join(project_dir, "uvicorn.log"), "a")
    subprocess.Popen(
        [python_bin, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=project_dir,
        stdout=uvicorn_log,
        stderr=uvicorn_log,
        start_new_session=True
    )
    time.sleep(2)

    print("🌐 啟動 ngrok 隧道...")
    ngrok_log = open(os.path.join(project_dir, "ngrok.log"), "a")
    subprocess.Popen(
        ["ngrok", "http", "127.0.0.1:8000"],
        cwd=project_dir,
        stdout=ngrok_log,
        stderr=ngrok_log,
        start_new_session=True
    )
    time.sleep(3)

    try:
        req = urllib.request.urlopen("http://127.0.0.1:8000/health")
        print(f"✅ FastAPI 健康檢查回應: {req.read().decode()}")
    except Exception as e:
        print(f"❌ FastAPI 健康檢查失敗: {e}")

    try:
        req_ngrok = urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels")
        content = req_ngrok.read().decode()
        import json
        tunnels = json.loads(content).get("tunnels", [])
        if tunnels:
            url = tunnels[0].get("public_url")
            print(f"🔗 LINE Developers Webhook URL 填寫網址:\n   {url}/webhook\n   (或填寫 {url} 皆可通過驗證！)")
    except Exception as e:
        print(f"⚠️ 讀取 ngrok 外網網址失敗: {e}")

if __name__ == "__main__":
    start_services()
