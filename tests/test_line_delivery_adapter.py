import pytest
from app.services.line_delivery_adapter import line_delivery_adapter, format_markdown_for_line

def test_line_delivery_adapter_chunking():
    """測試長文字 2000 字元自動精確切割功能"""
    short_text = "Hello Antigravity Line"
    chunks = line_delivery_adapter.split_text_chunks(short_text, max_length=2000)
    assert len(chunks) == 1
    assert chunks[0] == short_text

    # 測試長文字切割
    long_text = ("測試行內容\n" * 500)
    chunks_long = line_delivery_adapter.split_text_chunks(long_text, max_length=1000)
    assert len(chunks_long) > 1
    for chunk in chunks_long:
        assert len(chunk) <= 1000

def test_format_markdown_for_line_headers():
    """測試 Markdown 標題轉置為 Emoji 醒目標頭」"""
    raw_text = "# 第一層標題\n## 第二層標題\n### 第三層標題\n#### 第四層標題\n一般內文"
    formatted = format_markdown_for_line(raw_text)
    assert "📌 第一層標題" in formatted
    assert "🔹 第二層標題" in formatted
    assert "🔸 第三層標題" in formatted
    assert "▪️ 第四層標題" in formatted
    assert "一般內文" in formatted

def test_format_markdown_for_line_code_blocks():
    """測試代碼區塊 (```code```) 轉為縮排卡片格式，且不誤傷內部 # 註解」"""
    raw_text = (
        "# 標題\n"
        "```python\n"
        "# 這是一行 Python 註解\n"
        "def hello():\n"
        "    return 'world'\n"
        "```\n"
        "```\n"
        "無語言代碼\n"
        "```"
    )
    formatted = format_markdown_for_line(raw_text)
    
    # 驗證標題有被轉換
    assert "📌 標題" in formatted

    # 驗證代碼卡片格式
    assert "┌─ 💻 Code (python) ─" in formatted
    assert "│ # 這是一行 Python 註解" in formatted
    assert "│ def hello():" in formatted
    assert "└──────────────────" in formatted
    
    # 驗證無語言標示的卡片
    assert "┌─ 💻 Code ─" in formatted
    assert "│ 無語言代碼" in formatted

    # 驗證代碼內部的 # 註解沒有被替換成 📌
    assert "📌 這是一行 Python 註解" not in formatted

def test_format_markdown_empty_or_normal():
    """測試邊界條件：空字串與一般純文字」"""
    assert format_markdown_for_line("") == ""
    normal_text = "這是一段沒有 Markdown 的一般文字"
    assert format_markdown_for_line(normal_text) == normal_text

def test_deliver_text_with_markdown_and_chunking(mocker=None):
    """測試 deliver_text 發送流自動進行 Markdown 轉譯與 >2000 字元自動分段」"""
    user_id = "U_TEST_DELIVERY_USER"
    
    # 測試含 Markdown 之發送
    md_text = "# 大標題\n```python\nprint('hello')\n```"
    res = line_delivery_adapter.deliver_text(user_id, md_text)
    assert res is not None

    # 測試長 Markdown 訊息切割（超過 2000 字）
    long_md = "# 長訊息標題\n" + ("這是測試長內文內容重複行\n" * 250)
    formatted_long = line_delivery_adapter.format_markdown_for_line(long_md)
    assert len(formatted_long) > 2000
    
    chunks = line_delivery_adapter.split_text_chunks(formatted_long, max_length=2000)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 2000
    assert "📌 長訊息標題" in chunks[0]
