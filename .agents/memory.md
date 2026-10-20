# Memory (跨工作階段長期記憶索引)

本元件連結至專案根目錄之 [`AGENT_MEMORY.md`](../AGENT_MEMORY.md) 與 [`CONTEXT.md`](../CONTEXT.md)。

## 核心狀態追蹤清單
- **雲端工作目錄**：`/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line`
- **地端排程目錄**：`/Users/johnkuo/worktemp/Antigravity-Line`（系統 Crontab 實際執行路徑）
- **雙端同步鐵律**：任何程式碼與文檔修改完成後，必須 `git commit & push` 並於地端目錄執行 `git pull` 與回歸驗證。
