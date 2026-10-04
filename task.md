# 任務清單：根除解鎖誤打密碼漏洞與保障早安圖正常發送

- [ ] 1. 強化 `app/services/mac_unlocker.py`（加入黑白名單雙重防護與嚴格 Fail-Closed 熔斷）
- [ ] 2. 調整 `app/services/scheduler_service.py` 確保早安圖流程安全與優雅執行
- [ ] 3. 擴充單元測試 `tests/test_safe_mac_unlocker_unittest.py`（精確覆蓋本次截圖 LINE 聊天室與 Finder 情境）
- [ ] 4. 執行全套單元測試與安全驗證腳本
- [ ] 5. 執行 Private 目標早安圖發送測試，驗證正常發送不受影響
- [ ] 6. 提交變更並更新專案變動歷程
