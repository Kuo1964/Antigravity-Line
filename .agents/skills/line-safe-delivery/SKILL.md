---
name: line-safe-delivery
description: LINE 桌面版早安圖安全解鎖、精準搜尋、雙重熔斷核對與貼圖發送標準技能。
---

# LINE 安全發送標準工作流 (LINE Safe Delivery Skill)

## 標準執行步驟
1. **喚醒與鎖屏判定**：發送 `caffeinate -u -t 3`，透過 `CGSSessionScreenIsLocked` 與 Layer >= 1000 `loginwindow` 判定鎖定狀態。
2. **安全解鎖與輪詢**：通過白名單驗證後輸入密碼，並以最高 8 秒（每 0.5 秒一次）動態輪詢等待登入畫面淡出。
3. **強效置頂 LINE**：呼叫 `open -a LINE`、AppleScript `reopen` 與 `NSApplicationActivateIgnoringOtherApps`，並泵送 `NSRunLoop` 確認置頂。
4. **動態搜尋與回讀驗證**：動態讀取 `text field 1` 座標並點擊中心，貼上目標名稱後回讀 `value` 驗證吻合。
5. **實體點擊首項與 Vision OCR 核對**：實體點擊搜尋框下方首筆結果 `(sf_x + 100, sf_y + sf_h + 60)`，並以 `Vision` OCR 驗證聊天室標題包含目標名稱。
6. **對焦貼圖與發送**：點擊右側輸入框貼上圖片，等待 3.5 秒預覽載入後按 Return 送出（或於 `dry_run=True` 時保留供人工目視檢查）。
