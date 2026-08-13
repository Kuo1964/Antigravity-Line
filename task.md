# TICKET-003: LINE Markdown 格式化適配器開發任務

## 任務清單
- [x] 撰寫實作計畫 `implementation_plan.md` <!-- id: 0 -->
- [x] 在 `app/services/line_delivery_adapter.py` 實作 `format_markdown_for_line(text: str) -> str` 轉譯器 <!-- id: 1 -->
  - [x] 將 `# 標題` 轉換為帶有 Emoji 醒目標頭 (如 `📌 標題`) <!-- id: 2 -->
  - [x] 將代碼區塊 (```code```) 轉為縮排卡片格式 <!-- id: 3 -->
- [x] 確保 `deliver_text()` 在發送前自動調用 `format_markdown_for_line()` 適配，並於 >2000 字元時自動分段發送 <!-- id: 4 -->
- [x] 更新並擴充 `tests/test_line_delivery_adapter.py` 單元測試 <!-- id: 5 -->
- [x] 執行 pytest 驗證 100% 綠燈通過 <!-- id: 6 -->
- [ ] 回報結果至 Call Agent <!-- id: 7 -->
