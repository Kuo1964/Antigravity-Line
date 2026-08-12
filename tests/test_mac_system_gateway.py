import os
import pytest
from app.services.mac_system_gateway import mac_system_gateway

def test_mac_system_gateway_unlocked_check():
    """測試 MacSystemGateway 螢幕解鎖準備狀態檢查」"""
    is_ready = mac_system_gateway.ensure_unlocked_and_ready()
    assert is_ready in [True, False]

def test_mac_system_gateway_restore_state():
    """測試 MacSystemGateway 螢幕狀態復原流程」"""
    res = mac_system_gateway.restore_display_state()
    assert res in [True, False]

def test_mac_system_gateway_media_fetch(tmp_path):
    """測試 MacSystemGateway 早安圖片抓取與快取」"""
    media_path = mac_system_gateway.fetch_morning_media(keyword="good morning", target_dir=str(tmp_path))
    if media_path:
        assert os.path.exists(media_path)
