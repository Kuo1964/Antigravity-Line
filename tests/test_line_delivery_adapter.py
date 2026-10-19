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

def test_search_field_mismatch_triggers_fuse_and_blocks_sending():
    """測試：當搜尋框內文字為空或與目標好友不符時，觸發剛性安全熔斷，絕不貼圖送出」"""
    from unittest.mock import patch, MagicMock
    from app.services.line_desktop_controller import search_and_send_image
    
    with patch("app.services.line_desktop_controller.focus_line_app", return_value=True), \
         patch("app.services.line_desktop_controller.MacOSUIAdapter") as mock_adapter_cls, \
         patch("app.services.line_desktop_controller.get_line_search_field_info", return_value=((100, 100, 200, 30), "")): # 模擬搜尋框為空
        
        mock_adapter = MagicMock()
        mock_adapter_cls.return_value = mock_adapter
        mock_adapter.get_window_bounds.return_value = (0, 0, 1000, 800)
        
        # 目標為 Sophia Kuo，但搜尋框回傳 ""
        res = search_and_send_image(target_name="Sophia Kuo", image_path="/tmp/fake.jpg", dry_run=False)
        assert res is False
        # 確保絕無執行發送 KeyCode 36 (Return) 發送行為
        for call_args in mock_adapter.send_keycode.call_args_list:
            assert call_args[0][0] != 36

def test_search_field_match_allows_sending():
    """測試：當搜尋框內文字與 Vision 標題皆吻合目標好友時，通過驗證並順利執行」"""
    from unittest.mock import patch, MagicMock
    from app.services.line_desktop_controller import search_and_send_image
    
    with patch("app.services.line_desktop_controller.focus_line_app", return_value=True), \
         patch("app.services.line_desktop_controller.MacOSUIAdapter") as mock_adapter_cls, \
         patch("app.services.line_desktop_controller.verify_line_chat_title", return_value=True), \
         patch("app.services.line_desktop_controller.get_line_search_field_info", return_value=((100, 100, 200, 30), "Sophia Kuo")): # 模擬吻合
        
        mock_adapter = MagicMock()
        mock_adapter_cls.return_value = mock_adapter
        mock_adapter.get_window_bounds.return_value = (0, 0, 1000, 800)
        
        res = search_and_send_image(target_name="Sophia Kuo", image_path="", dry_run=True)
        assert res is True

def test_ocr_chat_title_mismatch_triggers_fuse_and_blocks_sending():
    """測試：當搜尋成功但右側聊天室標題 (Vision OCR) 判定非目標好友時，強制熔斷中止，絕不貼圖送出」"""
    from unittest.mock import patch, MagicMock
    from app.services.line_desktop_controller import search_and_send_image
    
    with patch("app.services.line_desktop_controller.focus_line_app", return_value=True), \
         patch("app.services.line_desktop_controller.MacOSUIAdapter") as mock_adapter_cls, \
         patch("app.services.line_desktop_controller.get_line_search_field_info", return_value=((100, 100, 200, 30), "Sophia Kuo")), \
         patch("app.services.line_desktop_controller.verify_line_chat_title", return_value=False): # 模擬標題不是目標對象
        
        mock_adapter = MagicMock()
        mock_adapter_cls.return_value = mock_adapter
        mock_adapter.get_window_bounds.return_value = (0, 0, 1000, 800)
        
        # 標題不吻合時，必須熔斷回傳 False
        res = search_and_send_image(target_name="Sophia Kuo", image_path="/tmp/fake.jpg", dry_run=False)
        assert res is False
        # 確保絕無執行發送 KeyCode 36 (Return) 發送行為
        for call_args in mock_adapter.send_keycode.call_args_list:
            assert call_args[0][0] != 36
