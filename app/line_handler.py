import logging
from typing import Optional
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from linebot.v3.exceptions import InvalidSignatureError
from app.config import settings

logger = logging.getLogger("line_handler")

# 初始化 Line WebhookHandler 與 MessagingApi
handler = WebhookHandler(settings.LINE_CHANNEL_SECRET) if settings.LINE_CHANNEL_SECRET else None

def get_messaging_api() -> Optional[MessagingApi]:
    """建立並回傳 Line MessagingApi 用戶端"""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        logger.warning("未設定 LINE_CHANNEL_ACCESS_TOKEN，無法推送 Line 訊息")
        return None
    config = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
    api_client = ApiClient(config)
    return MessagingApi(api_client)

def send_line_push_message(to_user_id: str, text: str) -> bool:
    """發送 Line Push Message 給指定使用者（自動處理超過 4500 字元的長訊息分段推播）"""
    messaging_api = get_messaging_api()
    if not messaging_api:
        logger.info(f"[模擬發送 Push Message 至 {to_user_id}]: {text}")
        return False
    
    try:
        # Line 限制單條訊息上限為 5000 字元，此處採用 4500 字元分段切片
        CHUNK_SIZE = 4500
        text_chunks = [text[i:i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        
        # 單次 PushMessageRequest 最多包含 5 條 TextMessage
        for batch_start in range(0, len(text_chunks), 5):
            batch = text_chunks[batch_start:batch_start + 5]
            messages = [TextMessage(text=chunk) for chunk in batch]
            push_request = PushMessageRequest(
                to=to_user_id,
                messages=messages
            )
            messaging_api.push_message(push_request)
            
        logger.info(f"成功發送 Push Message 至使用者 {to_user_id} (分段數: {len(text_chunks)})")
        return True
    except Exception as e:
        logger.error(f"發送 Line Push Message 失敗: {e}")
        return False
