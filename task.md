# 任務清單 (Task List)

- [x] 修復 `app/main.py`：背景任務與心跳全面改為 `await line_delivery_adapter.deliver_text_async`
- [x] 修復 `app/services/agent_session_engine.py`：為 Gemini 備用與降級呼叫加入 20 秒逾時保護
- [x] 徹底根除 LaunchAgent (`com.antigravity.linebot`) 前後台衝突引發的每秒自殺重生死循環 (Flapping Death Loop)
- [x] 驗證 LaunchAgent 常駐穩定性（日誌不再膨脹，Uvicorn PID 88372 與 ngrok PID 88377 長期穩定在線）
- [x] 執行 Git Commit 與 Push
