# AGENT_MEMORY.md (Antigravity 專案長期記憶庫)

本文件記載本專案的「硬性禁區」、「關鍵決策」與「已知環境陷阱」，供所有 Session 的 Agent 啟動時自動遵循，防止記憶衰退與重蹈覆轍。

---

## 🛑 禁區清單 (Forbidden Zones - 嚴禁擅自修改或破壞)
1. **早安圖與排程發送模組**：
   - 與主控 Agent 對話流程解耦，嚴禁破壞其定時產生與發送邏輯。
2. **Google Drive 工作目錄依賴**：
   - 專案路徑依賴 macOS CloudStorage 掛載，嚴禁將專案代碼硬編碼寫入臨時目錄（如 `/tmp` 或本機未同步目錄）。
3. **繁體中文與 Type Hints 規範**：
   - 所有的註解、文件、思考與對話全程強制繁體中文，所有 Python 函式必須具備完整 Type Hints。

---

## 💡 已驗證的核心架構決策 (Known Architecture Decisions)
1. **雙軌專案切換 (Dual-Track Context Engine)**：
   - `AgentSessionEngine` 同時支援「狀態鎖定 (`set_user_project`)」與「語意動態識別 (`detect_project_from_prompt`)」。
2. **LINE Markdown 格式化與 2000 字分段**：
   - 必須透過 `line_delivery_adapter.py` 進行 Emoji 與縮排卡片轉譯，超過 2000 字元自動分段連續發送。
3. **macOS 開關機時序與守護**：
   - 關機前 5 分鐘優雅釋放端口並退出；開機後守護行程具備 10 分鐘輪詢等待 Google Drive 磁碟就緒機制。

---

## 🩺 運行態除錯守則 (Runtime Guidelines)
1. **先跑 Doctor 再動手**：排查環境或服務前，優先執行 `./doctor.sh` 掌握端口與隧道狀態。
2. **先自檢再回報**：修改完 LINE 處理邏輯後，必須主動執行 `python -m tests.mock_line_webhook` 進行 Mock Webhook 驗證，禁止叫使用者手機盲測。
