# 導入計畫：LINE 全域搜尋動態座標定位與發送前文字回讀熔斷閘門

## 1. 事故背景與根因深度剖析 (Incident Analysis)
在 2026-10-18 21:30 排程執行時，原定送給 Sophia Kuo 的早安圖片，意外發送到了原本開著的「2026【第二十一屆賓航賓士高爾夫球隊】會務群組 (59)」。
經調閱當前 LINE Accessibility UI 架構與截圖分析，發現兩大致命死穴：
1. **寫死相對座標導致點擊搜尋框偏離**：
   原代碼使用固定偏移 `win_x + 190, win_y + 95`，算出的座標為 `(411, 187)`。而真實搜尋框邊界為 `Y: 159 ~ 197`，且上方有分類 Tab，點擊落在邊緣外側，**導致搜尋框根本未取得焦點**，截圖清楚可見搜尋框仍為灰色佔位字串 `🔍 搜尋聊天和訊息`。
2. **缺少目標聊天室與搜尋結果驗證機制**：
   搜尋框未聚焦的情況下，後續文字輸入與 Return 按鍵全數落空，畫面依然停留在上次使用者開啟的高爾夫球隊群組。隨後的貼圖與 Return 發送直接發給了該群組！

---

## 2. 解決方案與剛性防護架構 (Fail-Closed Architecture)

```
[ 啟動 LINE 桌面版並置頂 ]
         │
         ▼
[ 1. 動態向 Accessibility 查詢全域搜尋框真實邊界 (get_line_search_field_info) ]
   └── text field 1 of splitter group 1 of window 1
   └── 即時計算真實幾何中心 (如 422, 178) 並點擊 🎯
         │
         ▼
[ 2. 清空並輸入 target_name (Cmd+A ➜ Backspace ➜ Cmd+V) ]
         │
         ▼
[ 3. 🚨 剛性安全防線：即時回讀搜尋框文字 (current_search_val) ]
   ├── 若 target_name not in current_search_val:
   │     └── 立即觸發 CRITICAL 熔斷！中止任務，嚴禁貼圖送出！
   └── 若驗證通過:
         └── 繼續下一步
         │
         ▼
[ 4. 選取搜尋結果第一筆好友 ]
   └── 發送 KeyCode 125 (Down Arrow) 高亮第一項 ➜ KeyCode 36 (Return) 開啟聊天室
         │
         ▼
[ 5. 貼上早安圖片 (Cmd+V) 並在預覽後送出 (dry_run 模式則待命目視) ]
```

---

## 3. 測試與驗證結果 (Verification Status)

1. **單元測試 100% 綠燈**：
   - 增加 `test_search_field_mismatch_triggers_fuse_and_blocks_sending`（驗證搜尋框不吻合時強制熔斷）。
   - 增加 `test_search_field_match_allows_sending`（驗證吻合時正常流程）。
   - 全套 14 項單元測試全數 PASS。
2. **實機模擬貼圖驗證 (`scripts/simulate_paste_only.py`)**：
   - 即時取得搜尋框真實座標 `(295, 159, 254, 38)`，點擊中心點 `(422, 178)`。
   - 成功輸入 `Sophia Kuo` 並通過「步驟 B.1 驗證搜尋框當前輸入值: 'Sophia Kuo'」。
   - 精確開啟 Sophia Kuo 聊天室並將早安圖片貼入對話輸入框中！
3. **雲端與地端同步**：
   - GitHub main 分支與地端目錄 `/Users/johnkuo/worktemp/Antigravity-Line` 已完全對齊。
