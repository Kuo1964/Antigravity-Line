import os
import re
import time
import asyncio
import logging
from typing import List, Optional

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from linebot.v3.webhook import WebhookHandler

from app.config import settings
from app.services.line_desktop_controller import search_and_send_image
from app.services.execution_tracer import execution_tracer

logger = logging.getLogger("line_delivery_adapter")

def sanitize_text_for_line(text: str) -> str:
    """
    LINE API 文字安全清理器 (Sanitizer)：
    清理可能導致 LINE API 拋出 HTTP 400 Bad Request 的無效 Unicode 控制字元與不可見字元，
    確保發送內容 100% 符合 LINE API 規範。
    """
    if not text:
        return ""
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    return cleaned

def format_markdown_for_line(text: str) -> str:
    """
    格式化 Markdown 文字以適配 LINE 閱讀體驗：
    1. 將一至四級 Markdown 標題轉為 Emoji 醒目標頭 (📌 🔹 🔸 ▪️)
    2. 將 Markdown 代碼區塊 (```code```) 轉為美觀卡片縮排格式，且不誤傷程式碼內部 # 註解
    """
    if not text:
        return ""

    parts = re.split(r"(```[\s\S]*?```)", text)
    formatted_parts = []

    for part in parts:
        if part.startswith("```") and part.endswith("```"):
            code_block = part[3:-3]
            if code_block.startswith("\n"):
                code_block = code_block[1:]
            
            lines = code_block.split("\n")
            first_line = lines[0].strip() if lines else ""
            
            lang = ""
            code_lines = lines
            if first_line and re.match(r"^[a-zA-Z0-9_\+\#-]+$", first_line) and all(ord(c) < 128 for c in first_line):
                lang = first_line
                code_lines = lines[1:]

            header = f"┌─ 💻 Code ({lang}) ─" if lang else "┌─ 💻 Code ─"
            code_body = "\n".join([f"│ {l}" for l in code_lines])
            card = f"{header}\n{code_body}\n└──────────────────"
            formatted_parts.append(card)
        else:
            lines = part.split("\n")
            formatted_lines = []
            for line in lines:
                stripped = line.strip()
                if stripped.startswith("# "):
                    formatted_lines.append(f"📌 {stripped[2:]}")
                elif stripped.startswith("## "):
                    formatted_lines.append(f"🔹 {stripped[3:]}")
                elif stripped.startswith("### "):
                    formatted_lines.append(f"🔸 {stripped[4:]}")
                elif stripped.startswith("#### "):
                    formatted_lines.append(f"▪️ {stripped[5:]}")
                else:
                    formatted_lines.append(line)
            formatted_parts.append("\n".join(formatted_lines))

    result = "".join(formatted_parts).strip()
    return sanitize_text_for_line(result)

class LineDeliveryAdapter:
    """
    LINE 專屬訊息與多媒體傳輸適配器 (支援全非阻塞 deliver_text_async 與 Paced Streaming)。
    """

    def __init__(self):
        self.channel_access_token = settings.LINE_CHANNEL_ACCESS_TOKEN
        self.channel_secret = settings.LINE_CHANNEL_SECRET
        self._messaging_api = None
        self._handler = None

        if self.channel_access_token:
            config = Configuration(access_token=self.channel_access_token)
            api_client = ApiClient(config)
            self._messaging_api = MessagingApi(api_client)

        if self.channel_secret:
            self._handler = WebhookHandler(self.channel_secret)

    @property
    def messaging_api(self) -> Optional[MessagingApi]:
        return self._messaging_api

    @property
    def handler(self) -> Optional[WebhookHandler]:
        return self._handler

    def format_markdown_for_line(self, text: str) -> str:
        """導出內部 Markdown 格式化方法」"""
        return format_markdown_for_line(text)

    def split_text_chunks(self, text: str, max_length: int = 1800, max_chars: Optional[int] = None) -> List[str]:
        """
        語意段落安全拆分器 (Semantic Safe-Chunking):
        1. 優先依據雙換行 (\\n\\n) 或段落標籤進行切分。
        2. 若單一段落過長，再依據單換行 (\\n) 切分。
        3. 確保每個 chunk 不超過極限字數 (預設 1800 字)，相容 max_length 與 max_chars。
        """
        limit = max_chars if max_chars is not None else max_length
        if not text:
            return []
        if len(text) <= limit:
            return [text]

        chunks = []
        paragraphs = text.split("\n\n")
        current_chunk = ""

        for p in paragraphs:
            p_str = p.strip()
            if not p_str:
                continue

            if len(p_str) > limit:
                lines = p_str.split("\n")
                for line in lines:
                    if len(current_chunk) + len(line) + 1 > limit:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = line + "\n"
                    else:
                        current_chunk += line + "\n"
            else:
                if len(current_chunk) + len(p_str) + 2 > limit:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = p_str + "\n\n"
                else:
                    current_chunk += p_str + "\n\n"

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    async def deliver_text_async(self, to_user_id: str, text: str) -> bool:
        """
        全非阻塞異步發送介面：透過 asyncio.to_thread 發送 Messaging API，搭配 asyncio.sleep(0.5) 步調推播。
        """
        if not text:
            return False

        formatted_text = self.format_markdown_for_line(text)
        chunks = self.split_text_chunks(formatted_text, max_length=1800)

        execution_tracer.log_event("LINE_DELIVERY_PREPARE_ASYNC", {
            "to_user_id": to_user_id,
            "raw_text_length": len(text),
            "chunks_count": len(chunks)
        })

        if self._messaging_api:
            all_success = True
            for idx, chunk in enumerate(chunks):
                chunk_clean = sanitize_text_for_line(chunk)
                try:
                    push_request = PushMessageRequest(
                        to=to_user_id,
                        messages=[TextMessage(text=chunk_clean)]
                    )
                    await asyncio.to_thread(self._messaging_api.push_message, push_request)
                    execution_tracer.log_event("LINE_API_PUSH_SUCCESS_ASYNC", {
                        "to_user_id": to_user_id,
                        "chunk_index": idx + 1,
                        "total_chunks": len(chunks)
                    })
                    logger.info(f"成功透過異步 Messaging API 發送第 {idx + 1}/{len(chunks)} 段訊息至 {to_user_id}")
                except Exception as api_err:
                    execution_tracer.log_event("LINE_API_PUSH_ERROR_ASYNC", {
                        "to_user_id": to_user_id,
                        "error": str(api_err)
                    })
                    logger.warning(f"Messaging API 單段推播遭拒 ({api_err})，嘗試純文字降級安全重試...")
                    try:
                        plain_text = re.sub(r"[📌🔹🔸▪️┌─💻└─│]", "", chunk_clean).strip()
                        push_request_retry = PushMessageRequest(
                            to=to_user_id,
                            messages=[TextMessage(text=plain_text)]
                        )
                        await asyncio.to_thread(self._messaging_api.push_message, push_request_retry)
                    except Exception as retry_err:
                        all_success = False

                if len(chunks) > 1 and idx < len(chunks) - 1:
                    await asyncio.sleep(0.5)

            if all_success:
                return True

        if to_user_id and to_user_id.startswith("U") and len(to_user_id) >= 15:
            return False

        return await asyncio.to_thread(search_and_send_image, target_name=to_user_id, image_path="")

    def deliver_text(self, to_user_id: str, text: str) -> bool:
        """
        同步發送介面（維護既有相容性與測試相容）。
        """
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                asyncio.create_task(self.deliver_text_async(to_user_id, text))
                return True
        except RuntimeError:
            pass

        return asyncio.run(self.deliver_text_async(to_user_id, text))

    def deliver_image(self, to_user_id: str, image_path: str, caption: str = "") -> bool:
        """發送多媒體圖片訊息，整合桌面 GUI 自動化圖文發送能力 (早安圖片專用介面)"""
        logger.info(f"調用 LineDeliveryAdapter 發送圖片至 {to_user_id} (圖片: {image_path})")
        return search_and_send_image(target_name=to_user_id, image_path=image_path)

line_delivery_adapter = LineDeliveryAdapter()
