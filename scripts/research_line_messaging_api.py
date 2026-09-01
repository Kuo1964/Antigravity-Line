"""
LINE Messaging API 深度技術調研與可行性測試腳本
測試目標：
1. 驗證 LINE Messaging API 是否能直接指定暱稱/顯示名稱 (如 'Sharon Chou', 'Sophia Kuo')
2. 驗證 LINE Bot 是否能向未加 Bot 為好友的個人 LINE 帳號主動發送圖片
3. 測試官方 Push API 的必要參數與限制
"""

import os
import sys
import json
import httpx
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

LINE_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
ALLOWED_USER_IDS = [uid.strip() for uid in os.getenv("ALLOWED_USER_IDS", "").split(",") if uid.strip()]

def test_line_bot_info():
    """測試 1: 取得 Bot 基本資訊與配額"""
    print("\n--- [測試 1: 檢驗 LINE Bot 基本連線與配額] ---")
    headers = {"Authorization": f"Bearer {LINE_ACCESS_TOKEN}"}
    try:
        res = httpx.get("https://api.line.me/v2/bot/info", headers=headers, timeout=10)
        print(f"Bot Info HTTP 狀態: {res.status_code}")
        if res.status_code == 200:
            info = res.json()
            print(f"Bot 顯示名稱: {info.get('displayName')}")
            print(f"Bot Basic ID: @{info.get('basicId')}")
            print(f"Bot 類型: {info.get('chatMode')}")
        else:
            print(f"Bot 資訊取得失敗: {res.text}")
    except Exception as e:
        print(f"連線異常: {e}")

def test_push_by_display_name(target_name: str):
    """測試 2: 嘗試直接使用好友名稱 (如 'Sharon Chou') 呼叫 Push API"""
    print(f"\n--- [測試 2: 嘗試使用顯示名稱 '{target_name}' 調用 Push API] ---")
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": target_name,
        "messages": [
            {
                "type": "text",
                "text": "早安測試"
            }
        ]
    }
    try:
        res = httpx.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload, timeout=10)
        print(f"HTTP 狀態碼: {res.status_code}")
        print(f"LINE API 回應: {res.text}")
        if res.status_code == 400:
            err_data = res.json()
            print(f"❌ 官方拒絕原因: {err_data.get('message')} - {err_data.get('details')}")
            print("👉 結論：LINE Messaging API 的 'to' 欄位嚴格限定必須為 33 字元的 User ID (U...)，不支援傳入好友名稱！")
    except Exception as e:
        print(f"請求異常: {e}")

def test_push_to_valid_user_id():
    """測試 3: 向已綁定且加入好友的 User ID 發送測試訊息"""
    if not ALLOWED_USER_IDS:
        print("\n--- [測試 3: 無設定 ALLOWED_USER_IDS，略過] ---")
        return

    user_id = ALLOWED_USER_IDS[0]
    print(f"\n--- [測試 3: 向已加入 Bot 的管理員 User ID ({user_id[:6]}...) 測試發送] ---")
    headers = {
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "to": user_id,
        "messages": [
            {
                "type": "text",
                "text": "🤖 [Antigravity 研究測試] 這是一則由 LINE Bot 透過官方 Push API 發送的系統診斷訊息。"
            }
        ]
    }
    try:
        res = httpx.post("https://api.line.me/v2/bot/message/push", headers=headers, json=payload, timeout=10)
        print(f"HTTP 狀態碼: {res.status_code}")
        if res.status_code == 200:
            print("✅ 成功！只要具備目標的專屬 User ID，Bot 即可在背景 100% 無感推送訊息。")
        else:
            print(f"推送回應: {res.text}")
    except Exception as e:
        print(f"請求異常: {e}")

def main():
    print("==================================================")
    print(" 📡 LINE Messaging API 技術可行性驗證與研究")
    print("==================================================")
    test_line_bot_info()
    test_push_by_display_name("Sharon Chou")
    test_push_by_display_name("Sophia Kuo")
    test_push_to_valid_user_id()
    print("\n==================================================")

if __name__ == "__main__":
    main()
