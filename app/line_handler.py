import logging
from typing import Optional
from app.services.line_delivery_adapter import line_delivery_adapter

logger = logging.getLogger("line_handler")

# 向下相容屬性
handler = line_delivery_adapter.handler

def get_messaging_api():
    return line_delivery_adapter._messaging_api

def send_line_push_message(to_user_id: str, text: str) -> bool:
    """代理呼叫 LineDeliveryAdapter 之深層發送入口"""
    return line_delivery_adapter.deliver_text(to_user_id, text)
