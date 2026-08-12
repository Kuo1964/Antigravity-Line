# V15 架構深層化計畫：macOS UI Controller Deepening

太棒了！這是這份架構報告中最具價值的一項重構。這個重構將建立一道完美乾淨的「接縫 (Seam)」，大幅提升未來我們撰寫自動化腳本的「槓桿效應 (Leverage)」與維護的「局部性 (Locality)」。

## 🎯 重構目標
將 `line_desktop_controller.py` 中與「底層 macOS 作業系統互動」的髒程式碼（ctypes C 語言呼叫、AppleScript 字串拼接）全數抽離，封裝進一個全新且獨立的 `MacOSUIAdapter` 模組中。

這會將原本的 **Shallow Module (淺層模組)** 轉變為具有 **Deep Interface (深層介面)** 的架構。

---

## 🛠️ Proposed Changes (預期修改範圍)

### [NEW] `app/services/macos_ui_adapter.py`
建立這個全新的 Adapter 模組。它將封裝系統底層的複雜度，並對外提供一個乾淨的深層介面：
- `native_click(x: int, y: int)`：封裝 CoreGraphics 的 C-types 呼叫。
- `reopen_app(app_name: str)`：封裝 activate 與 reopen 的 AppleScript。
- `unhide_window(app_name: str)`：封裝 AXHidden 取消隱藏的邏輯。
- `get_window_bounds(app_name: str) -> tuple`：封裝擷取視窗座標的機制，並內建重試 (Retry) 邏輯。
- `send_keystroke(keys: str, using_cmd: bool = False)`：封裝鍵盤按鍵模擬。
- `send_keycode(keycode: int)`：封裝鍵盤 KeyCode 模擬 (如 Backspace=51, Return=36)。

### [MODIFY] `app/services/line_desktop_controller.py`
徹底淨化這個模組，刪除所有 ctypes 與 `subprocess.run(["osascript"...])` 的呼叫。
- 將 `focus_line_app()` 與 `search_and_send_image()` 改寫為純商業邏輯。
- 這些商業邏輯只會透過呼叫 `MacOSUIAdapter` 暴露出來的高階方法來完成任務。

---

## ❓ Open Questions (需要您決定的架構設計問題)

在動手之前，身為架構引導者，我有幾個關於「介面設計」的問題想請您定奪（這也是 `/grilling` 流程的一環）：

1. **依賴注入 (Dependency Injection) 的方式**
   您希望在 `line_desktop_controller.py` 中，是直接 `import MacOSUIAdapter` 作為一個靜態工具模組來呼叫？還是希望把它實例化為一個物件 `adapter = MacOSUIAdapter()`，讓未來的測試更容易進行 Mock？*(建議：實例化為物件，未來測試 Leverage 較高)*

2. **Retry 機制的歸屬 (Locality)**
   我們之前為了防止剛解鎖時 AppleScript 反應慢，在抓取座標時加入了 `retries=10` 的重試機制。您認為這個「重試機制」是屬於 macOS 系統層的責任（應該封裝在 Adapter 裡），還是屬於 LINE 發送流程的商業責任（應該留在 Controller 裡）？*(建議：放在 Adapter 裡，讓 Adapter 自己處理系統的不可靠性)*

---

## User Review Required

> [!IMPORTANT]
> 這是一次純粹的「架構重構 (Refactoring)」，完成後系統的行為與功能不會有任何改變，但程式碼的健康度與擴充性會大幅提升。
> 
> 請問您對上方的 **Open Questions** 有什麼偏好的決定嗎？（若無特別偏好，我將採用上述的「建議」做法）。
> 請您審閱計畫並回覆您的決定，或直接點擊 **Proceed** 讓我採用建議做法為您執行！
