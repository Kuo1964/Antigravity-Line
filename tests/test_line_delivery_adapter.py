import pytest
from app.services.line_delivery_adapter import line_delivery_adapter

def test_line_delivery_adapter_chunking():
    """測試長文字 2000 字元自動精確切割功能」"""
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

def test_line_delivery_adapter_deliver():
    """測試 deliver_text 發送流」"""
    user_id = "U_TEST_DELIVERY_USER"
    res = line_delivery_adapter.deliver_text(user_id, "測試 LineDeliveryAdapter 訊息發送")
    assert res is not None
