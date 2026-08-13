## CONTEXT_MAP.md

### Overview
Antigravity-Line 是一個 macOS 環境下的雙向 AI Agent 控制與自動化推播系統。本專案包含兩大核心領域：
1. **LINE Webhook 即時對話與推播模組**：基於 FastAPI 秒回 HTTP 200 OK 搭配 `BackgroundTasks` 異步推播模式，提供雙向控制 Antigravity Agent 進行多專案開發、指令查詢與對話。
2. **自動早安排程與電源控制模組 (Scheduling Consolidation)**：負責讀取 `schedule_tasks.json` 單一事實來源，將早安圖文發送時間轉換為 macOS 底層喚醒 (`pmset`)、防睡眠與排程執行 (`crontab`)。

---

### Target Area 1: 自動排程模組 (Scheduling Consolidation - 早安訊息專用)
- **進入點**: `scripts/setup_daily_schedule.sh` (由開發者手動執行)
- **部署核心**: `scripts/deploy_schedule.py`
- **邏輯配接器**: `app/services/scheduler_adapter.py`

### Target Area 2: LINE Bot 訊息傳送與 Webhook 入口模組 (Line Messaging Entry)
- **進入點**: `app/main.py`
- **對話與任務引擎**: `app/agent_manager.py` (Thin Facade) / `app/services/agent_session_engine.py` (Deep Engine)
- **發送適配器**: `app/line_handler.py` (Thin Facade) / `app/services/line_delivery_adapter.py` (Deep Adapter)

---

### Component Tree
```text
Antigravity-Line 系統架構
├── [領域 1] LINE Webhook 即時推播 (app/main.py)
│   ├── [SHARED] app.config.settings (環境變數、白名單驗證與安全設定)
│   ├── [SHARED] app.agent_manager.agent_manager (Thin Facade 對話/任務管理器)
│   │   └── app.services.agent_session_engine.agent_session_engine (深層對話與 Context 引擎)
│   ├── [SHARED] app.project_manager.project_manager (工作區多專案掃描與語意切換)
│   └── [SHARED] app.line_handler.send_line_push_message (推播發送 Thin Facade)
│       └── app.services.line_delivery_adapter.line_delivery_adapter (深層訊息適配與 GUI 降級)
│
└── [領域 2] 自動早安排程模組 (scripts/setup_daily_schedule.sh)
    └── scripts/deploy_schedule.py (Python 進入點)
        └── app.services.scheduler_adapter.scheduler_adapter [SHARED]
            ├── app/config/schedule_tasks.json (排程時間與目標設定檔)
            ├── scripts/schedule_next_wake.sh (Root Crontab 中使用的喚醒接力腳本)
            └── app/services/mac_system_gateway.py (macOS 螢幕解鎖與早安圖片爬取閘道器)
```

---

### Data Flow

#### Flow 1: 早安訊息自動排程流程
1. **讀取設定**: `scheduler_adapter.py` 的 `load_tasks()` 讀取 `schedule_tasks.json`。
2. **時間計算**: 針對每組任務，解析 `send_time` (發送時間) 與 `wake_time` (喚醒時間)，並動態計算下一次的 `caffeinate` 與 Root 喚醒接力時間。
3. **替換與防護**: 將計算好的排程指令，透過 `_replace_crontab_block()` 放入 `# --- Antigravity Line START ---` 與 `END` 區塊中。
4. **底層寫入**: 透過 `subprocess` 呼叫 `crontab -` (User Crontab) 與 `sudo crontab -` (Root Crontab) 進行系統級寫入。
5. **啟動循環與發送**: 呼叫 `pmset repeat cancel` 並設定第一個喚醒時間；觸發時調用 `send_daily_morning_card.py` 經由 `mac_system_gateway` 與 `line_delivery_adapter` 進行早安圖文推播。

#### Flow 2: Webhook 即時訊息與 Agent 處理流程
1. **HTTP 請求進入**: LINE 伺服器發送 `POST /webhook` 請求至 `app/main.py:webhook()`。
2. **白名單驗證**: 調用 `settings.is_user_allowed(user_id)` 檢驗 LINE User ID。
3. **內建指令分發**: 若為 `/reset`、`/projects`、`/use`、`/status` 或 `/help`，直接由主線程調用 `send_line_push_message()` 即時回應。
4. **異步任務派發**: 若為一般 Agent 需求，調用 `background_tasks.add_task(process_background_agent_task, user_id, user_text)`。
5. **秒回回應**: `main.py` 立即回傳 `JSONResponse({"status": "ok"}, 200)` 給 LINE 伺服器。
6. **背景執行與推播**: `process_background_agent_task()` 呼叫 `agent_manager.run_agent_task()` 完成推論後，調用 `send_line_push_message()` 推播結果至使用者 LINE。

---

### Shared Assets and Blast Radius

- **`app/services/scheduler_adapter.py` [SHARED System Level]**
  - **影響範圍**：會直接修改開發者 macOS 本機的 User Crontab 與 Root Crontab。
  - **防呆機制**：依賴 `MARKER_START` 與 `MARKER_END` 區塊標記，嚴禁全域覆寫。
- **`app/config/schedule_tasks.json` [SHARED]**
  - **影響範圍**：發送模組 (`send_daily_morning_card.py`) 預期此設定檔中的 `target` 名稱精確對應 LINE 桌面版聯絡人。
- **`app/config/settings.py` [SHARED Across App]**
  - **影響範圍**：`app/main.py`, `agent_session_engine.py`, `line_delivery_adapter.py`, `project_manager.py`。修改白名單或服務配置會同時影響 API 推播與早安圖文排程。
- **`app/line_handler.py` / `line_delivery_adapter.py` [SHARED Across App]**
  - **影響範圍**：`app/main.py`, `app/scheduler.py`, `app/services/scheduler_service.py`。修改訊息推播適配器會影響即時回復與早安卡片推播。
- **`app/agent_manager.py` / `agent_session_engine.py` [SHARED Across App]**
  - **影響範圍**：`app/main.py`, `tests/test_basic.py`, `tests/test_project_manager.py`。修改會衝擊 AgentSessionEngine 對態推論與單元測試。

---

### Conventions and Tribal Knowledge
- **安全標記 (Safe Marker)**：任何對 Crontab 的覆寫都必須包裝在 `# --- Antigravity Line START ---` 區塊內。
- **提權機制**：排程設定涉及 `pmset` 與 root crontab，執行時必須透過 `sudo` 提權 (`setup_daily_schedule.sh`)。
- **異步防逾時機制**：LINE Webhook 有 5 秒回應限制，非指令任務必須放在 `BackgroundTasks` 中執行。
- **繁體中文與日誌規範**：所有系統輸出、對話回應與程式碼註解必須使用繁體中文。
- **版本歷史雙備份**：重構或重大計畫需同時維持根目錄 Artifact 與帶日期副檔名備份（如 `implementation_plan_YYYYMMDD.md`）。
- **單元測試指令**：使用 `./venv/bin/python -m pytest tests/` 執行全套測試（維持 22/22 全綠燈通過）。

---

### Staleness Rules
本 Context Map 於以下情境需進行更新：
1. 修改 macOS 自動排程機制（如改用 `launchd` 取代 `cron`）或變更排程設定檔格式時。
2. `app/main.py` 中的端點路由或 BackgroundTasks 處理邏輯發生變動時。
3. 任一 `[SHARED]` 資產（`scheduler_adapter`, `agent_manager`, `line_handler`, `project_manager`）的介面發生重構時。

*(Last verified: 2026-08-13, against main branch)*
