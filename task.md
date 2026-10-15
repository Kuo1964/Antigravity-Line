# 任務清單：修復鎖定螢幕無人值守自動解鎖與置頂發送早安圖全流程

- [x] 1. 深度診斷 2026-10-14 21:30 Sophia Kuo 早安圖片未發送故障根因（Quartz 字典延遲與登入畫面遮罩問題）
- [x] 2. 強化 `app/services/mac_unlocker.py`：
  - [x] 加入 `loginwindow` / `screensaverengine` 前台即時優先判斷，徹底防止將鎖定狀態誤判為未鎖定
  - [x] 重構 `get_frontmost_app_name()`，採用 macOS WindowServer (CoreGraphics Quartz) 原生實時視窗查詢，解決 Cocoa AppKit 在無 RunLoop 環境下的記憶體快取停滯問題
  - [x] 識別 Layer >= 1000 之系統登入遮罩層，防止穿透誤讀底層桌面視窗（如 Antigravity）觸發黑名單熔斷
  - [x] 引入解鎖後 8 秒動態輪詢等待機制，相容 macOS 登入視窗淡出過渡動畫時間
- [x] 3. 強化 `app/services/line_desktop_controller.py`：
  - [x] 置頂重試提升至 6 次，並在輪詢中泵送 `NSRunLoop` 刷新系統狀態
  - [x] 透過實時 WindowServer 視窗屬主辨識 LINE 置頂狀態，消除無效熔斷
- [x] 4. 單元測試強化與環境隔離：
  - [x] 新增 `test_locked_screen_detected_via_frontmost_loginwindow` 單元測試
  - [x] 隔離原生 Quartz 檢查，全套 12 項單元測試 100% 綠燈通過
- [x] 5. 雲端與地端雙向同步：
  - [x] GitHub main 分支推送最新提交
  - [x] 地端排程目錄 (`/Users/johnkuo/worktemp/Antigravity-Line`) 完成 `git pull` 同步
- [x] 6. 實機鎖定全自動貼圖模擬測試（`dry_run=True`）驗證通過：
  - [x] 自動喚醒螢幕 ➜ 自動輸入密碼解鎖 ➜ 下載早安圖 ➜ 喚起 LINE 一次置頂 ➜ 搜尋 Sophia Kuo ➜ 貼入圖片待命
  - [x] 使用者親眼目視確認早安圖已成功貼在 Sophia Kuo 對話輸入框中
