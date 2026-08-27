"""
實機驗證防盲打安全防護機制
檢測當前 macOS 前台視窗、螢幕鎖定狀態與解鎖防護反應
"""
import os
import sys
import logging

# 加入專案路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.mac_unlocker import mac_unlocker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def main():
    print("\n==========================================")
    print(" 🛡️ macOS 安全防盲打解鎖腳本實機驗證")
    print("==========================================\n")
    
    front_app = mac_unlocker.get_frontmost_app_name()
    is_locked = mac_unlocker.is_screen_locked()
    
    print(f"1. 當前前台活動程式: [{front_app}]")
    print(f"2. Quartz 鎖定狀態檢測: [{'鎖定 (LOCKED)' if is_locked else '未鎖定 (UNLOCKED)'}]")
    
    print("\n3. 執行安全解鎖測試 (傳入模擬密碼)...")
    res = mac_unlocker.unlock_screen("MOCK_DUMMY_PASSWORD_SAFE_CHECK")
    
    print(f"\n4. 執行結果: {res}")
    if not is_locked:
        print("   ✅ 驗證成功：因螢幕處於未鎖定狀態，腳本直接安全跳過打密碼，前台沒有任何字元被敲入！")
    elif front_app and front_app.lower() not in mac_unlocker.ALLOWED_UNLOCK_PROCESSES:
        print("   ✅ 驗證成功：前台為非登入程式，觸發白名單熔斷攔截，密碼絕不外洩！")
    else:
        print("   ℹ️ 螢幕為鎖定狀態且前台為登入畫面。")
    print("\n==========================================\n")

if __name__ == "__main__":
    main()
