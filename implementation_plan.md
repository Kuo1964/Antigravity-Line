# 導入計畫：macOS 鎖定狀態無人值守自動解鎖與 LINE 早安圖發送流程修復

## 1. 問題概述 (Background & Root Causes)
在 2026-10-14 21:30 排程執行時，發送給 Sophia Kuo 的早安圖片未能送出。經系統日誌深度剖析與實機測試，鎖定了三大核心根因：
1. **鎖定狀態誤判 (Quartz 字典字串延遲)**：
   原先 `is_screen_locked()` 僅依賴字串比對 `CGSSessionScreenIsLocked = 1`，在背景定時喚醒無 GUI 上下文環境下容易漏判，誤判為「未鎖定」而跳過密碼輸入步驟。
2. **Cocoa AppKit 記憶體快取停滯**：
   在 CLI Python 腳本（非 GUI App）中，缺少持續運行的 `NSRunLoop`，導致 `NSWorkspace.sharedWorkspace().frontmostApplication()` 停留在第一次呼叫時獲取的 `loginwindow`，即使螢幕已成功登入並切換至桌面，依然返回舊值導致逾時熔斷。
3. **macOS 視窗層級 (Window Layer) 穿透問題**：
   `loginwindow`（鎖定畫面）的視窗層級在 Layer 2000 以上。使用純 Layer 0 查詢會直接穿透遮罩層讀取到背景底層應用程式（如 Antigravity），觸發密碼輸入黑名單熔斷。

---

## 2. 解決方案架構 (Solution Architecture)

```
[ 排程觸發 / 定時喚醒 ]
         │
         ▼
[ 1. 喚醒螢幕 (caffeinate) ]
         │
         ▼
[ 2. 鎖定狀態精確檢測 (mac_unlocker) ]
   ├── 檢查 CGSSessionScreenIsLocked == 1
   └── 檢查 WindowServer Layer >= 1000 遮罩層 (loginwindow)
         │
    (確認鎖定)
         ▼
[ 3. 安全自動解鎖 (unlock_screen) ]
   ├── 嚴格白名單校驗 (前台確認為 loginwindow)
   ├── 模擬輸入密碼 + Return (key code 36)
   └── 8 秒動態輪詢等待登入淡出過渡動畫完成
         │
    (確認解鎖完成)
         ▼
[ 4. 抓取早安圖 (image_crawler) ]
   └── 下載最新 Bing 圖片並寫入剪貼簿
         │
         ▼
[ 5. 置頂 LINE 桌面版 (line_desktop_controller) ]
   ├── 啟動 / 還原視窗 (open -a LINE / reopen)
   ├── 泵送 NSRunLoop 刷新系統狀態
   └── 實時檢查 WindowServer Layer 0 最頂層視窗屬主是否為 LINE (最多重試 6 次)
         │
    (確認置頂成功)
         ▼
[ 6. 精確點擊搜尋與貼圖 (macos_ui_adapter) ]
   ├── 點擊全域搜尋框座標 ➜ 貼上 "Sophia Kuo" ➜ Return 開啟聊天室
   └── 點擊右側對話框輸入區 ➜ Cmd + V 貼上圖片 (dry_run 模式保留目視)
```

---

## 3. 測試與驗證結果 (Verification & Status)

1. **單元測試全數通過**：
   - `tests/test_safe_mac_unlocker_unittest.py`：覆蓋白名單解鎖、黑名單熔斷、None 阻斷、loginwindow 識別、Fail-Closed 防護等 7 項測試全數 PASS。
   - `tests/test_line_delivery_adapter.py` 等模組測試通過，總計 12 項測試全數 `OK`。
2. **實機鎖定模擬測試 (`dry_run=True`)**：
   - 螢幕鎖定（`Ctrl+Cmd+Q`）後，系統自動喚醒、自動輸入密碼進入桌面、喚起 LINE（一次置頂成功）、搜尋 Sophia Kuo 並將早安圖片精準貼入對話輸入框中。
   - 使用者已目視確認早安圖在輸入框內就位完畢！
3. **雲端與地端同步**：
   - 雲端 GitHub main 與地端目錄 `/Users/johnkuo/worktemp/Antigravity-Line` 已完全對齊最新代碼。
