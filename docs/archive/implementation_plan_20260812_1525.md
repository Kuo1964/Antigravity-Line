# V14.2 LINE 視窗喚醒失敗分析與修正測試計畫 (測試分支)

非常感謝您進行測試並提供完整的錯誤 Log，這個測試結果對我們非常有價值，直接幫我們排除了錯誤的方向！

## 🔍 失敗原因分析：為什麼 `Command + 1` 沒用？

根據 AppleScript 的運作底層邏輯，我們送出 `Command + 1` 卻沒有反應，原因出在 **「事件攔截 (Event Routing)」**：

在 macOS 中，如果一個應用程式（如 Safari 或 LINE）沒有任何開啟的視窗，當我們透過腳本送出快捷鍵時，這個指令會直接丟給「頂部選單列 (Menu Bar)」。
但是！LINE 是一套跨平台的應用程式，它的開發團隊並沒有把 `Command + 1` 綁定在頂部選單列上，而是**綁定在「視窗本身」**。
👉 **結論：因為當時沒有視窗，所以 `Command + 1` 就像丟進了黑洞，LINE 根本沒有接收到這個快捷鍵！**

---

## 💡 下一步解決思路 (V14.2 測試計畫)

既然「假裝按鍵盤」這招行不通，我們必須改用 macOS 最正統的「原生物理邏輯」。

當您平時用滑鼠去點擊下方 Dock 上的 LINE 圖示時，即使視窗被關了，它也會乖乖跳出來。在 macOS 底層，這個「點擊 Dock 圖示」的動作，發送的是一個叫作 **`reopen`** 的專屬 AppleEvent 指令。

### 🛠️ 驗證計畫 (即將修改測試腳本，不動主程式)：

我將修改 `temp_test/test_line_reopen.py` 測試腳本，把原本送出快捷鍵的動作，替換成 macOS 最純粹的原生指令：
```applescript
tell application "LINE"
    activate
    reopen
end tell
```
這個指令在系統底層的意義等同於**「幫我點一下 Dock 上的 LINE 圖示」**。

---

## User Review Required

> [!IMPORTANT]
> 我們找出了快捷鍵被吃掉的原因，接下來將測試改用系統原生的 `reopen` 指令來模擬點擊 Dock。
> 此計畫依然只會在 `temp_test/test_line_reopen.py` 測試分支中進行，絕對不會動到主程式。
> 
> 請問您是否同意這個 V14.2 分析與測試方向？
> 如果您同意，請點擊 **Proceed**，我馬上為您修改測試腳本！
