# Spec: LINE Bot ↔ Antigravity 2.0 雙向協同系統規格書 (SPEC.md)

本文件綜合 `/grill-with-docs` 訪談結果與 `docs/CONTEXT.md` 之 6 大架構決策 (ADR-001 ~ ADR-006)，定稿 LINE Bot 聊天機器人與 Antigravity 2.0 雙向協同系統之軟體需求與測試規格說明。

- **版本**: 1.0.0
- **最後更新時間**: 2026-08-13
- **狀態**: `ready-for-agent`

---

## 1. Problem Statement (問題陳述)

目前開發者在使用 Antigravity 2.0 Agent 控制多專案開發與查看進度時，必須固定坐在 Mac 電腦前操作 Terminal。當開發者離座、行動中或使用手機時，無法隨時下達專案指令、查詢 Agent 執行狀態，亦無法在遠端即時接收 Antigravity 執行的成果反饋與錯誤告警。

---

## 2. Solution (解決方案)

建置 **LINE Bot ↔ Antigravity 2.0 雙向協同運作系統**。開發者可透過手邊的 LINE 行動 App：
1. 傳送對話或專案控制指令至手邊運行的 Antigravity。
2. 切換或鎖定目標專案工作區（支援狀態鎖定與 Prompt 語意自動辨識雙軌制）。
3. 即時收到 Antigravity 執行的進度心跳 (Progress Heartbeat) 與成果推播。
4. 在涉及高風險寫入/代碼變更指令時，收到自動推播的 confirmation 訊息，回覆 `YES` 後授權執行，兼具便利性與安全防禦。

---

## 3. User Stories (使用者故事清單)

1. **As a** 開發者, **I want to** 在 LINE 上發送指令給指定專案, **so that** 我能在離座時讓 Antigravity 遠端執行建置、測試與分析。
2. **As a** 開發者, **I want to** 使用 `/use <專案名>` 手動鎖定目標專案, **so that** 後續所有對話指令均預設對該專案發效。
3. **As a** 開發者, **I want to** 在 Prompt 中直接提及專案名稱（如「在 Portugal_Paris-2026 查行程」）, **so that** 系統能智慧切換並自動注入該專案的工作區檔案脈絡。
4. **As a** 開發者, **I want to** 在發送指令後於 1 秒內收到「接單成功」回應, **so that** 我確定請求已進入伺服器佇列且 LINE 連線不會逾時。
5. **As a** 開發者, **I want to** 在耗時較長的 Agent 任務執行中每隔 15 秒收到狀態心跳提示, **so that** 我清楚掌握任務目前推進的階段。
6. **As a** 開發者, **I want to** 收到排版良好的成果推播（包含轉換後的 Emoji 標題與縮排代碼卡片）, **so that** 我在手機畫面上能輕鬆閱讀複雜的推論與 Log 成果。
7. **As a** 開發者, **I want** 超過 2000 字元的長成果自動被分段推播, **so that** 訊息不會因為 LINE 官方字數限制而被截斷丟失。
8. **As a** 開發者, **I want to** 在下達包含代碼修改或檔案刪除之高風險指令時收到確認訊息, **so that** 系統不會在未經授權下誤刪或修改原始碼。
9. **As a** 開發者, **I want to** 回覆 `YES` 後解凍並執行待確認的高風險任務, **so that** 我能掌握關鍵邊界的控制權。
10. **As a** 開發者, **I want** 系統為我的 LINE User ID 建立獨立任務鎖, **so that** 在上一任務執行完成前不會因為重複發送指令而引發競態幹擾。
11. **As a** 開發者, **I want** 系統將 Session 與鎖定專案寫入本地 `app/data/sessions.json`, **so that** FastAPI 服務重啟後對話與狀態不會遺失。

---

## 4. Implementation Decisions (實作決策)

- **控制與發送介面層 (Web & Dispatch Layer)**:
  - 擴充 `app/main.py` Webhook 路由，維持秒回 HTTP 200 OK 搭配 `BackgroundTasks` 的異步調用模式。
  - 將專案切換、指令解析與訊息發送統一收攏於 `LineDeliveryAdapter` (`deliver_text`, `deliver_image`)。
- **對話與任務引擎層 (Agent & Session Engine Layer)**:
  - 在 `AgentSessionEngine` 內部擴充 **三段式進度心跳推播機制 (Progress Heartbeat)**，定期透過發送通道回報進度。
  - 導入 **Gemini 輕量意圖分類器 (High-Risk Intent Classifier)**，於任務執行前解析需求是否屬於 Code-Mutation / File-Deletion；若屬於高風險類別，將任務寫入待確認佇列並推播 confirmation 訊息。
- **持久化與隊列層 (Persistence & Queue Layer)**:
  - 建立 `SessionStore` 管理器，每次 Session 對話歷史或專案鎖定更新時，異步唯讀寫入 `app/data/sessions.json`。
  - 為每位 `user_id` 維護 asyncio Task Lock，防止並行任務競態。

---

## 5. Testing Decisions (測試與切縫決策)

- **測試原則**: 採行為導向與黑盒/灰盒切縫測試，不測試私有實作細節，僅針對外部介面與發送合約進行驗證。
- **主要測試切縫 (Testing Seams)**:
  - `tests/test_agent_session_engine.py`: 驗證雙軌專案切換、Session 重置與意圖分類鎖定。
  - `tests/test_line_delivery_adapter.py`: 驗證 Markdown 格式化轉換與 2000 字元分段切分邏輯。
  - `tests/test_webhook.py`: 驗證 Webhook 秒回 HTTP 200 OK、白名單驗證與指令分發。
- **既有測試參照 (Prior Art)**:
  - 遵循現有 22 個 `pytest` 測試架構，維持 100% 綠燈通過。

---

## 6. Out of Scope (非本次範圍)

- **發送早安圖片與自動喚醒排程程式** (`send_daily_morning_card.py`, `scheduler_adapter.py`, `schedule_tasks.json`)：已設為系統絕對紅線，不在此 Spec 修改範圍內。
- **多圖富文字 Flex Message 畫布編輯器**：本次專注於標準圖文與分段推播卡片，不引入複雜 Flex Message JSON Schema。

---

## 7. Further Notes (補充說明)

- 實作時需確保 `app/data/` 目錄若不存在時自動建立，並將 `app/data/*.json` 加入 `.gitignore` 防止洩漏隱私。
