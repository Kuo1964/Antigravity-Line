# 任務清單：根除 LINE 搜尋偏差誤發群組漏洞與強化搜尋回讀熔斷閘門

- [x] 1. 深度診斷 2026-10-18 21:30 早安圖片誤發至「高爾夫球隊群組」之致命根因（寫死相對座標 Y 軸偏移導致未點入搜尋框，且缺少目標標題/搜尋結果驗證機制）
- [x] 2. 透過 macOS Accessibility System Events 探測 LINE 搜尋框架構：
  - [x] 確定全域搜尋框為 `text field 1 of splitter group 1 of window 1`
  - [x] 取得真實動態絕對座標 `(295, 159, 254, 38)`，點擊中心點 `(422, 178)`
- [x] 3. 重構 `app/services/line_desktop_controller.py`：
  - [x] 實裝 `get_line_search_field_info()` 動態獲取搜尋框座標與當前值
  - [x] 加入「步驟 B.1 搜尋文字回讀剛性熔斷閘門」：若搜尋框文字未包含目標好友，立即中止任務，絕不貼圖送出
  - [x] 加入「向下鍵 (KeyCode 125)」選取搜尋結果第一筆再按 Enter，確保切換至目標好友聊天室
- [x] 4. 新增與執行單元測試：
  - [x] `tests/test_line_delivery_adapter.py` 新增搜尋框不吻合熔斷與吻合發送之雙重單元測試
  - [x] 全套 14 項單元測試 100% 綠燈通過
- [x] 5. 雲端與地端雙向同步：
  - [x] GitHub main 分支推送最新提交（`74b047d`）
  - [x] 地端排程目錄 (`/Users/johnkuo/worktemp/Antigravity-Line`) 完成 `git pull` 同步
- [x] 6. 實機執行模擬貼圖測試驗證：
  - [x] 實時取得搜尋框座標並精確點擊中心點
  - [x] 成功輸入 `Sophia Kuo` 並通過「步驟 B.1 驗證搜尋框當前輸入值: 'Sophia Kuo'」
  - [x] 成功切換至 Sophia Kuo 聊天室並將早安圖片貼入對話輸入框待命（未發送）
