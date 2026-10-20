# Tool Guidance (工具呼叫精準指引)

1. **精準檢索 (Scoped Search)**：禁止在整個專案目錄下無差別搜尋，應先閱讀 `README.md`、`CONTEXT.md` 鎖定目標模組。
2. **禁止盲猜 UI 座標**：操作 macOS 桌面應用程式時，優先透過 Accessibility (`System Events`) 或 `Quartz.CGWindowListCopyWindowInfo` 動態取得真實座標，並泵送 `NSRunLoop` 防止快取停滯。
3. **沙盒與地端同步**：操作地端排程目錄 `/Users/johnkuo/worktemp/Antigravity-Line` 時，應明確申請權限並確認雙端 Git Commit Hash 一致。
