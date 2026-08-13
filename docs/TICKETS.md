# Tracer-Bullet Tickets 清單: LINE Bot ↔ Antigravity 2.0 雙向協同 (TICKETS.md)

本檔案將 `docs/SPEC.md` 的 11 項 User Stories 與實作決策，拆解為 6 個具備清晰依賴關係 (Blocking Edges) 的小顆粒度任務 Ticket。每個 Ticket 均為獨立可驗證、可單獨由 `/implement` 執行與進行 Code Review 的微型模組。

- **日期**: 2026-08-13
- **規格檔依據**: [`docs/SPEC.md`](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/docs/SPEC.md)

---

## 📌 Ticket 概覽與依賴圖 (Dependency Map)

```text
[Ticket 1: SessionStore 持久化] ──┐
                                  ├──> [Ticket 2: 雙軌專案綁定] ──┬──> [Ticket 4: 高風險二次確認] ──┐
[Ticket 3: LINE Markdown 適配] ──┼───────────────────────────────┴──> [Ticket 5: 三段式異步心跳] ──┼──> [Ticket 6: 整合驗收 & 綠燈防禦]
```

---

## 🎫 Ticket 1: 建立 SessionStore 持久化管理器與資料結構
- **ID**: `TICKET-001`
- **阻擋需求 (Blockers)**: 無 `[NO BLOCKERS]`
- **範疇 (Scope)**:
  - 建立 `SessionStore` (`app/services/session_store.py`)，將使用者的 Session 與當前鎖定專案寫入/讀取 `app/data/sessions.json`。
  - 確保 `app/data/` 目錄存在，並在 `.gitignore` 加入 `app/data/*.json` 保護隱私。
- **測試切縫 (Testing Seam)**: `tests/test_session_store.py` (測試寫入、讀取與重啟恢復)。
- **驗收標準**: 單元測試 100% 通過，成功存取 `sessions.json`。

---

## 🎫 Ticket 2: 擴充 AgentSessionEngine 支援雙軌專案綁定與歷史 Context
- **ID**: `TICKET-002`
- **阻擋需求 (Blockers)**: `TICKET-001`
- **範疇 (Scope)**:
  - 更新 `AgentSessionEngine` 整合 `SessionStore`。
  - 實現 `/use <專案名>` 狀態鎖定與 Prompt 專案名稱語意比對雙軌切換機制。
- **測試切縫 (Testing Seam)**: `tests/test_agent_session_engine.py`。
- **驗收標準**: `test_agent_session_engine.py` 綠燈通過，專案切換順暢。

---

## 🎫 Ticket 3: 實現 LINE 專用 Markdown 格式化適配器與長字數分段
- **ID**: `TICKET-003`
- **阻擋需求 (Blockers)**: 無 `[NO BLOCKERS]`
- **範疇 (Scope)**:
  - 在 `LineDeliveryAdapter` 擴充 Markdown 格式轉譯器（`# 標題` -> `📌 標題`,代碼塊轉為卡片）。
  - 保證字數 >2000 時自動精確拆分為多段發送。
- **測試切縫 (Testing Seam)**: `tests/test_line_delivery_adapter.py`。
- **驗收標準**: `test_line_delivery_adapter.py` 綠燈通過，長字數拆分與格式化轉譯正常。

---

## 🎫 Ticket 4: 實現 Gemini 輕量級意圖分類器與高風險二次確認機制
- **ID**: `TICKET-004`
- **阻擋需求 (Blockers)**: `TICKET-002`
- **範疇 (Scope)**:
  - 在 `AgentSessionEngine` 加入二元意圖判定 (Read-Only vs Code-Mutation/Delete)。
  - 判定為高風險時，暫存任務並向 LINE 發送 confirmation 訊息，待使用者回覆 `YES` 後解凍執行。
- **測試切縫 (Testing Seam)**: `tests/test_agent_session_engine.py`。
- **驗收標準**: 嘗試刪除/修改動作時正確觸發二次確認，回覆 `YES` 後繼續執行。

---

## 🎫 Ticket 5: 實現三段式異步進度心跳推播與互斥鎖
- **ID**: `TICKET-005`
- **阻擋需求 (Blockers)**: `TICKET-002`, `TICKET-003`
- **範疇 (Scope)**:
  - 在 `app/main.py` 與 `process_background_agent_task` 實現秒回接單 (200 OK)、每 15 秒進度心跳推播。
  - 為每個 `user_id` 維護任務互斥鎖，避免重複執行競態。
- **測試切縫 (Testing Seam)**: `tests/test_webhook.py`。
- **驗收標準**: 1 秒內秒回 HTTP 200 OK，長任務每 15 秒產生進度推播。

---

## 🎫 Ticket 6: 全套功能整合驗收與 22/22 測試綠燈防禦
- **ID**: `TICKET-006`
- **阻擋需求 (Blockers)**: `TICKET-001`, `TICKET-002`, `TICKET-003`, `TICKET-004`, `TICKET-005`
- **範疇 (Scope)**:
  - 執行全套 `pytest` 測試與端對端連線驗證。
  - 確保 100% 不損害早安排程與全套舊測試案例。
- **測試切縫 (Testing Seam)**: 全套 `pytest tests/`。
- **驗收標準**: `pytest` 保持 22/22 全數綠燈通過。
