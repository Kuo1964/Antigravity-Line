# Guardrails (安全防護欄與 Fail-Closed 熔斷規範)

## 1. 預算與工具呼叫控制
- **工具呼叫上限**：單一高階任務連續呼叫工具次數嚴禁超過 8 次。
- **防止死循環**：連續 3 次返回相同錯誤訊息時必須立即中止並回報。

## 2. macOS 螢幕解鎖安全防線
- **白名單強制檢驗**：僅允許在最上層為 `loginwindow` 或 `screensaverengine`（含 Layer >= 1000 遮罩）時模擬鍵盤輸入密碼。
- **黑名單即時熔斷**：若前台為 `LINE`、`Finder`、`Antigravity`、`Terminal` 等一般應用程式，嚴禁輸出任何密碼字元。

## 3. LINE 自動化發送雙重剛性熔斷閘門
- **第一道閘門（搜尋框回讀驗證）**：點擊並輸入目標名稱後，必須回讀 `text field 1 of splitter group 1 of window 1` 的 `value`；若未包含目標名稱，立即觸發 `CRITICAL` 熔斷退出。
- **第二道閘門（Vision OCR 標題視覺核對）**：點擊首筆搜尋結果開啟聊天室後，必須透過 `screencapture -l <wid>` 與 Apple `Vision` 框架辨識視窗文字；若未包含目標好友名稱，立即觸發 `CRITICAL` 熔斷，絕不貼圖與發送。
