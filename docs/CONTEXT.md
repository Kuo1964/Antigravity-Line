# Antigravity Line Bot 雙向協同系統架構文檔 (CONTEXT.md)

本文件紀錄 LINE Bot 聊天機器人與 Antigravity 2.0 雙向協同運作系統之領域通用語言 (Glossary)、系統邊界與核心架構決策 (Architecture Decision Records, ADR)。

- **版本**: 1.0.0
- **最後更新時間**: 2026-08-13
- **驗證分支**: `main`

---

## 📖 領域通用語言 (Domain Glossary)

- **AgentSessionEngine**: 對話與任務調度核心引擎，負責管理對話歷史、自動 Workspace 脈絡注入與意圖判定。
- **LineDeliveryAdapter**: 訊息與媒體發送適配器，封裝 LINE Messaging API 與 macOS 桌面 GUI 自動化發送，處理 2000 字元分段推播。
- **ProjectBindingMode**: 專案綁定模式。支援 `/use <專案名>` 狀態鎖定與 Prompt 語意思考自動切換之雙軌機制。
- **ProgressHeartbeat**: 異步任務心跳進度推播，避免長耗時任務引起連線端逾時疑慮。
- **HighRiskConfirmation**: 高風險指令二次確認機制。針對 Code-Mutation 或寫入指令，系統先發送 confirmation 訊息，待使用者回覆 `YES` 後才執行。

---

## 🏛️ 架構決策紀錄 (Architecture Decision Records, ADR)

### ADR-001: 專案綁定與切換機制 (Project Context Binding)
- **狀態**: 已核可 (Accepted)
- **決策**: 採「狀態鎖定 (`/use <專案名>`)」與「語意自動比對」雙軌制。
- **動機**: 使用者既能強制固定某一目標專案，也能在對話中直接提及專案名快速傳送指令。

### ADR-002: 三段式異步狀態推播 (Three-Phase Async Progress)
- **狀態**: 已核可 (Accepted)
- **決策**: 
  1. 秒回 200 OK 接單提示。
  2. 每 15 秒推播一次「進度心跳」。
  3. 任務完成推播最終成果。
- **動機**: 解決 LINE Webhook 5 秒連線逾時限制，同時給予使用者即時狀態反饋。

### ADR-003: LINE 專屬 Markdown 格式化適配 (LINE Markdown Adapter)
- **狀態**: 已核可 (Accepted)
- **決策**: 在 `LineDeliveryAdapter` 內部將 Markdown 標題轉為 Emoji 格式，代碼轉為縮排卡片，超過 2000 字元自動分段。
- **動機**: 提升成果在行動端 LINE App 上的閱讀體驗。

### ADR-004: 高風險寫入指令二次確認機制 (High-Risk Intent Confirmation)
- **狀態**: 已核可 (Accepted)
- **決策**: 由 Gemini 進行意圖二元分類 (Read-Only vs Code-Mutation)，若涉及寫入/刪除，先推播 confirmation 訊息待使用者回覆 `YES` 後執行。
- **動機**: 防止遠端指令誤刪原始碼或執行破壞性指令。

### ADR-005: 使用者層級任務佇列與互斥鎖 (User-Level Task Locking)
- **狀態**: 已核可 (Accepted)
- **決策**: 為每位 LINE 白名單使用者建立獨立的任務鎖，同一使用者一次僅處理一個任務，重疊發送時給予佇列提示。
- **動機**: 確保對話歷史與工作區操作不發生競態干擾。

### ADR-006: 本地狀態持久化 (Local State Persistence)
- **狀態**: 已核可 (Accepted)
- **決策**: 將 Session 對話歷史與當前鎖定專案狀態同步寫入 `app/data/sessions.json`。
- **動機**: 確保 FastAPI 服務重啟後，對話脈絡不會斷層。
