# 任務清單：根除解鎖誤打密碼漏洞與保障早安圖正常發送

- [x] 1. 強化 `app/services/mac_unlocker.py`（加入黑白名單雙重防護與嚴格 Fail-Closed 熔斷）
- [x] 2. 調整 `app/services/mac_system_gateway.py` 與 `app/services/mac_unlocker.py` 去除發送完成後的螢幕鎖定行為
- [x] 3. 擴充單元測試 `tests/test_safe_mac_unlocker_unittest.py`（精確覆蓋 LINE 聊天室、Finder、None 前台與去除鎖定等情境）
- [x] 4. 執行全套單元測試與 Project Doctor 診斷（100% 綠燈通過）
- [x] 5. 提交最新程式碼並推送至遠端 GitHub
