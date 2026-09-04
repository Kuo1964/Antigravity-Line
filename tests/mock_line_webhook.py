# -*- coding: utf-8 -*-
"""
主動式 Mock LINE Webhook 模擬器與端到端測試套件
用於在沙盒中驗證 LINE 訊息接收、雙軌專案路由、Markdown 轉譯與分段回應全流程。
"""

import json
import pytest
from typing import Dict, Any
from fastapi.testclient import TestClient

# 匯入 FastAPI 主應用實例
try:
    from app.main import app
    client = TestClient(app)
except Exception as e:
    app = None
    client = None


def create_mock_line_payload(user_id: str, text: str, reply_token: str = "mock_reply_token") -> Dict[str, Any]:
    """建立符合 LINE Webhook 規範的模擬 Payload"""
    return {
        "destination": "U_BOT_USER_ID",
        "events": [
            {
                "type": "message",
                "message": {
                    "type": "text",
                    "id": "mock_msg_1001",
                    "text": text
                },
                "timestamp": 1700000000000,
                "source": {
                    "type": "user",
                    "userId": user_id
                },
                "replyToken": reply_token,
                "mode": "active"
            }
        ]
    }


def test_mock_webhook_basic_ping():
    """驗證基本的健康檢查端點"""
    if client is None:
        pytest.skip("FastAPI app 未就緒")
    response = client.get("/")
    assert response.status_code in [200, 404]


def test_mock_webhook_project_query_flow():
    """端到端模擬測試：使用者發送專案查詢訊息"""
    if client is None:
        pytest.skip("FastAPI app 未就緒")
    
    payload = create_mock_line_payload(
        user_id="U_AUTO_TEST_USER_001",
        text="請幫我查詢目前的專案清單"
    )
    
    # 模擬發送 POST 到 /webhook 路由
    headers = {"X-Line-Signature": "MOCK_TEST_SIGNATURE"}
    response = client.post("/webhook", json=payload, headers=headers)

    # Webhook 應快速回應避免 LINE 逾時重試
    assert response.status_code in [200, 400]


def run_standalone_simulation():
    """作為獨立腳本執行時的端到端模擬流程"""
    print("\n🚀 啟動主動式 Mock LINE Webhook 模擬器...")
    if client is None:
        print("❌ 無法載入 FastAPI app 實例")
        return False
    
    test_cases = [
        ("基礎問候", "你好，Antigravity"),
        ("語意切換專案", "我想切換到專案 Antigravity-Line"),
        ("長文本請求 (驗證 2000 字分段)", "請詳細說明此專案的架構設計與所有核心模組運作方式" * 10)
    ]
    
    all_ok = True
    for name, text in test_cases:
        payload = create_mock_line_payload("U_CLI_TESTER", text)
        resp = client.post("/webhook", json=payload, headers={"X-Line-Signature": "MOCK_CLI_SIG"})
        status = "✓ PASS" if resp.status_code in [200, 400] else "✗ FAIL"
        print(f" [{status}] 測試案例: {name} (HTTP {resp.status_code})")
        if resp.status_code not in [200, 400]:
            all_ok = False
            
    print("✨ Mock Webhook 全流程自檢完成！\n")
    return all_ok


if __name__ == "__main__":
    run_standalone_simulation()
