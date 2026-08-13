# TICKET-003 實作計畫 (Implementation Plan)

## 背景與目標
LINE 平台本身對 Markdown 語法支援有限。為了確保在 LINE 聊天室中顯示美觀、專業且易讀的訊息，我們需要在 `LineDeliveryAdapter` 中實作 Markdown 適配轉譯器 `format_markdown_for_line`，將 Markdown 語法（例如 `# 標題`、```代碼區塊```）轉換為 LINE 優化的格式（Emoji 標號、縮排卡片格式），並在 `deliver_text()` 發送前自動適配與處理分段。

## 變更項目

### 1. `app/services/line_delivery_adapter.py`
- 新增 `format_markdown_for_line(text: str) -> str` 方法與模組獨立函式：
  - **標題轉換**：使用正則表達式或逐行解析，將 `# 標題` 轉為 `📌 標題`，`## 標題` 轉為 `🔹 標題`，`### 標題` 轉為 `🔸 標題`。
  - **代碼區塊轉換**：正則擷取 ```[lang]\ncode\n``` 區塊，轉為帶邊框/縮排的卡片格式：
    ```
    ┌─ 💻 Code (lang) ─
    │ code line 1
    │ code line 2
    └──────────────────
    ```
- 修改 `deliver_text(self, to_user_id: str, text: str) -> bool`：
  - 在執行訊息切割與推播前，先調用 `format_markdown_for_line(text)` 將訊息格式化。
  - 保留 2000 字元自動分段切割推播邏輯。

### 2. `tests/test_line_delivery_adapter.py`
- 新增 `test_format_markdown_for_line_headers()`：驗證 `#`, `##`, `###` 轉為帶 Emoji 的醒目標頭。
- 新增 `test_format_markdown_for_line_code_blocks()`：驗證代碼區塊轉換為縮排卡片格式。
- 新增 `test_deliver_text_with_markdown()`：驗證 `deliver_text` 呼叫時會自動進行 Markdown 轉化與 >2000 字元分段。

## 驗證流程
- 執行 `./venv/bin/python -m pytest tests/test_line_delivery_adapter.py` 確保 100% 通過。
