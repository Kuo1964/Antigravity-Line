# ADR 0002: 建立專案可觀測性與健康診斷器 (Project Health Doctor)

## 狀態 (Status)
已接受 (Accepted) - 2026-08-19

## 背景 (Context)
歷史對話中曾多次因 Google Drive 磁碟未掛載、本地 Port 8000 佔用、ngrok 隧道異常或 LINE API Token 失效而導致除錯陷入死循環與多輪盲測。

## 決策 (Decision)
1. 在專案內實作 `app/doctor.py` 與 `./doctor.sh` 單鍵健康檢測工具。
2. 檢測項目嚴格局限於本專案範圍，包含：
   - Google Drive 掛載與目錄讀寫可達性
   - Port 8000 佔用狀態與進程 PID 診斷
   - ngrok tunnel 狀態與公開網址健康度
   - LINE Channel Access Token / Secret 設定格式檢核
   - macOS `pmset` 關機/開機排程時序比對
3. Agent 在執行重大變更或排查啟動問題前，優先調用 Doctor 指令。

## 後果 (Consequences)
- **正面**：1 秒內定位是環境問題還是代碼問題，消除「使用者手機盲測」造成的無效等待。
- **限制**：僅讀取本專案與本地相關進程，不干涉或影響系統其他獨立專案。
