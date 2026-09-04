# 專案領域術語表 (Domain Glossary)

本文件定義 `Antigravity-Line` 及自動化防護體系中的核心概念與通用詞彙 (Ubiquitous Language)。

---

## 核心術語 (Core Terms)

### 1. Safe Guardrail (安全防護欄)
一套將棕地專案變更分為 **四階段閉環** 的全自動審查機制：
1. **Reconnaissance (程式碼偵查)**：探索架構與依賴邊界，繪製影響地圖。
2. **Change-Spec (變更規格化)**：將模糊需求轉換為具備邊界約束與防破壞規範的規格。
3. **Code Review (自動化代碼審查)**：比對修改前後，驗證是否符合防破壞承諾。
4. **Regression Verification (回歸驗證)**：透過沙盒自動執行單元測試與環境驗證，確認無副作用。

### 2. Project Doctor (專案健康診斷器)
專門用於評估專案運行環境、依賴就緒狀態與外部服務連通性的單鍵診斷工具（`app/doctor.py`）。
涵蓋：Google Drive 磁碟掛載、本地服務端口、ngrok 隧道、LINE API 金鑰與開關機排程時序。

### 3. Graceful Lifecycle (優雅生命週期守護)
針對 macOS 排程開關機（`pmset`）與雲端硬碟延遲掛載設計的時序協調機制：
- 關機前 5 分鐘主動釋放端口並退出服務。
- 開機 10 分鐘內輪詢等待 Google Drive 磁碟就緒後再啟動 Antigravity 服務。

### 4. Dual-Track Session (雙軌上下文切換)
- **狀態鎖定 (State Locked)**：明確將 LINE Bot 與特定專案進行持久化綁定。
- **語意動態 (Semantic Dynamic)**：依據使用者訊息內容自動動態路由至目標專案，不破壞當前對話歷史。
