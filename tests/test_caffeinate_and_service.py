import os
import sys
import time
import subprocess
import httpx
import pytest

def test_caffeinate_is_running():
    """驗證 caffeinate 防休眠機制是否可正常被系統啟動"""
    proc = subprocess.Popen(["caffeinate", "-dimsu", "-t", "5"])
    time.sleep(1)
    # 檢查進程是否正在執行中
    assert proc.poll() is None, "caffeinate 應該在運作中"
    proc.terminate()

def test_fastapi_and_webhook():
    """驗證 FastAPI Webhook 端點運作"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    
    # 1. 測試健康檢查端點
    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "ok"

    # 2. 測試 Webhook 端點傳送 /status 指令
    payload = {
        "events": [
            {
                "type": "message",
                "message": {"type": "text", "text": "/status"},
                "source": {"userId": "U1234567890abcdef1234567890abcdef"}
            }
        ]
    }
    webhook_res = client.post("/webhook", json=payload)
    assert webhook_res.status_code == 200
    assert webhook_res.json()["status"] == "ok"
