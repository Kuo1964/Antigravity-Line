## Guardrail Spec: 修復 Line Bot 訊息傳送連線

### Task
診斷並修復無法透過 LINE Bot 傳送訊息至 Antigravity 的問題。透過健全化服務一鍵啟動腳本 (start.sh) 與驗證 Webhook 入口 (app/main.py)，確保 FastApi 與 ngrok 外網隧道穩定在背景運行，達到 LINE App 訊息秒回與背景異步推播。

### Read First
- `app/main.py` (FastAPI Webhook 入口與指令處理解耦)
- `start.sh` (背景服務與 ngrok 一鍵管理腳本)
- `app/services/line_delivery_adapter.py` (訊息推播與長訊息拆分適配器)
- `docs/CONTEXT_MAP.md` (專案脈絡地圖)

### Follow These Patterns
- **FastAPI 異步解耦**：非指令回應必須使用 `BackgroundTasks` 在背景派發推論任務，主 thread 必須立即回應 HTTP 200 OK。
- **白名單安全檢查**：使用 `settings.is_user_allowed(user_id)` 進行第一線權限防禦。

### Reuse, Do Not Rebuild
- **連線啟動**：複用並擴充 `start.sh` 進行進程喚起與 Port 8000 保護。
- **訊息適配器**：使用 `line_delivery_adapter.deliver_text()` 與 `deliver_image()`，嚴禁在入口處重新發明 LINE Push API 呼叫。

### Absolutely Do Not Touch
- **早安圖片與自動喚醒排程程式 (系統紅線)**：
  - 🛑 `scripts/send_daily_morning_card.py`
  - 🛑 `app/services/scheduler_adapter.py`
  - 🛑 `app/config/schedule_tasks.json`
  - 🛑 `scripts/setup_daily_schedule.sh`
  - 🛑 `scripts/schedule_next_wake.sh`
- **全域權限與金鑰名稱**：`.env` 檔案內既有之欄位名稱（如 `LINE_CHANNEL_SECRET`, `ALLOWED_USER_IDS`）。
- **對話引擎壓減演算法**：`app/services/agent_session_engine.py` 內部之對話歷史 Context 壓縮邏輯。

### Slices
- **Slice 1 (Plan & Reconnaissance)**：
  - 檢視全系統運行狀態、連線埠與 `.env` 配置。提出完整的服務啟動與連線修復計畫，**不安裝或修改任何代碼**。
- **Slice 2 (Service Startup & Tunnel Setup)**：
  - 確保 `start.sh` 正確啟動 FastAPI 與 ngrok 背景進程，並取得動態 ngrok URL。
- **Slice 3 (Webhook Communication Verification)**：
  - 驗證 `app/main.py` `/webhook` 端點回應性與 LINE 訊息派發。
- **Slice 4 (Full Verification & Test Suite Pass)**：
  - 執行 `./venv/bin/python -m pytest tests/`，確保全套 22 個測試全數綠燈通過。

### Acceptance Criteria
1. **服務正常連線**：`http://127.0.0.1:8000/health` 回傳 `status: ok`。
2. **ngrok 隧道在線**：`http://127.0.0.1:4040/api/tunnels` 成功取得公開 HTTPS URL。
3. **Webhook 異步秒回**：模擬向 `/webhook` 發送 POST 測試請求，服務需在 1 秒內回傳 HTTP 200 OK。
4. **測試套件 100% 通過**：執行全套 `pytest` 保持 22/22 全通過。

### What NOT To Do
- ❌ **絕對不可更動早安排程模組**：嚴禁改動任何早安卡片發送與 macOS crontab 喚醒排程代碼。
- ❌ **絕對不可重構無關模組**：嚴禁為了修復連線而重構 `project_manager.py` 或 Agent 邏輯。
- ❌ **絕對不可引入未定義的第三方程式庫**。
