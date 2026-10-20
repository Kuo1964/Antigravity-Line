# AGENT_MEMORY.md (Antigravity 專案長期記憶庫 - Harness² 演化版)

本文件記載本專案的「硬性禁區」、「關鍵決策」與「經實證驗證之環境教訓 (Evidence-Supported Lessons)」，由 **Harness² 編排層級遞迴 (Experience Reflector)** 持續沉澱，供所有 Session 的 Agent 啟動時自動遵循，防止記憶衰退與重蹈覆轍。

---

## 🛑 禁區清單 (Forbidden Zones - 嚴禁擅自修改或破壞)
1. **早安圖與排程發送模組**：
   - 與主控 Agent 對話流程解耦，嚴禁破壞其定時產生與發送邏輯。
2. **Google Drive 工作目錄與地端雙向同步依賴**：
   - 雲端工作目錄（Google Drive）與地端排程目錄（`/Users/johnkuo/worktemp/Antigravity-Line`，系統 Crontab 指向處）必須保持 100% 同步。每次修改完成後必須執行 `git commit & push` 並於地端 `git pull`。
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

## 🔬 Harness² 實證經驗教訓庫 (Evidence-Supported Lessons)

### 教訓 1：macOS 鎖定畫面視窗層級 (Window Layer >= 1000) 與狀態檢測
- **根因**：在 crontab 無 GUI 環境下單純依賴子進程解析 `CGSSessionScreenIsLocked = 1` 容易漏判；且鎖定時底層桌面視窗（Layer 0，如 Antigravity）未關閉，若僅查 Layer 0 會穿透 `loginwindow`（Layer 2001/2004）誤觸黑名單熔斷。
- **鐵律**：檢查螢幕鎖定與前台行程時，必須優先檢測 `CGSSessionScreenIsLocked == 1` 與 `kCGWindowLayer >= 1000` 的 `loginwindow` 遮罩層，並在輸入密碼後進行最高 8 秒動態輪詢等待過渡動畫完成。

### 教訓 2：CLI Python 腳本之 Cocoa `NSRunLoop` 快取停滯問題
- **根因**：非 GUI 的命令列 Python 腳本沒有持續運行的 Cocoa 事件循環，`NSWorkspace.sharedWorkspace().frontmostApplication()` 會永遠停留在第一次讀取的快取（如 `loginwindow`）。
- **鐵律**：查詢最頂層應用程式時，必須優先使用 `Quartz.CGWindowListCopyWindowInfo`（WindowServer 硬實時查詢），若呼叫 `NSWorkspace` 則必須先執行 `NSRunLoop.currentRunLoop().runUntilDate_` 泵送事件刷新狀態。

### 教訓 3：LINE 搜尋框動態定位與雙重剛性熔斷閘門 (Fail-Closed Gates)
- **根因**：固定相對座標偏移易因工具列變動而點偏；且在搜尋文字框內按鍵盤 `Down Arrow` 僅移動文字游標，無法選取下方搜尋結果列表，導致停留在舊聊天室誤發圖片。
- **鐵律**：
  1. **動態座標定位**：透過 System Events 讀取 `text field 1 of splitter group 1 of window 1` 取得真實座標並點擊幾何中心。
  2. **第一道熔斷（搜尋框文字回讀）**：輸入目標名稱後立即回讀 `value`，若未包含目標名稱則立即 `CRITICAL` 熔斷退出。
  3. **實體點擊首項結果**：直接點擊搜尋框正下方 60px 處 `(sf_x + 100, sf_y + sf_h + 60)` 開啟首筆搜尋結果。
  4. **第二道熔斷（Vision OCR 標題視覺核對）**：貼圖前透過 `screencapture -l <wid>` 與 Apple 原生 `Vision` 框架辨識視窗文字，確認包含目標聯絡人名稱才允許貼圖與發送。

---

## 🩺 運行態除錯守則 (Runtime Guidelines)
1. **先跑 Doctor 與 Harness Probe 再動手**：排查環境或修改配置後，優先執行 `./venv/bin/python scripts/verify_harness_probe.py` 驗證 8 大元件、依賴與雲地端同步狀態。
2. **先自檢再回報**：修改完 LINE 發送或 Webhook 邏輯後，必須主動執行單元測試與 `simulate_paste_only.py`（`dry_run=True`），禁止未經探針驗證即交付。
