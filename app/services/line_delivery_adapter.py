import logging
from typing import List, Optional
from linebot.v3 import WebhookHandler
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)
from app.config import settings

logger = logging.getLogger("line_delivery_adapter")

class LineDeliveryAdapter:
    """
    高槓桿、深介面 LineDeliveryAdapter 模組。
    統一 LINE Messaging API 與 macOS 桌面 GUI 自動發送入口，
    自動處理 2000 字元長訊息分段切割與 API 失敗時的桌面 GUI 自動化降級。
    """

    def __init__(self):
        self._handler: Optional[WebhookHandler] = None
        self._messaging_api: Optional[MessagingApi] = None
        self._init_sdk()

    def _init_sdk(self):
        """初始化 Line SDK 實例」"""
        if settings.LINE_CHANNEL_SECRET:
            self._handler = WebhookHandler(settings.LINE_CHANNEL_SECRET)
        if settings.LINE_CHANNEL_ACCESS_TOKEN:
            config = Configuration(access_token=settings.LINE_CHANNEL_ACCESS_TOKEN)
            api_client = ApiClient(config)
            self._messaging_api = MessagingApi(api_client)

    @property
    def handler(self) -> Optional[WebhookHandler]:
        return self._handler

    def split_text_chunks(self, text: str, max_length: int = 2000) -> List[str]:
        """內部私有方法：自動按 LINE 字元上限精確切割長訊息"""
        if not text:
            return []
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        curr = ""
        lines = text.split("\n")
        for line in lines:
            if len(curr) + len(line) + 1 <= max_length:
                curr += (line + "\n")
            else:
                if curr:
                    chunks.append(curr.strip())
                # 若單行即超過 max_length
                if len(line) > max_length:
                    for i in range(0, len(line), max_length):
                        chunks.append(line[i:i+max_length])
                    curr = ""
                else:
                    curr = line + "\n"
        if curr.strip():
            chunks.append(curr.strip())
        return chunks

    def format_markdown_for_line(self, text: str) -> str:
        """
        將 Markdown 格式轉譯為適合 LINE 顯示的樣式。
        - 將 `# 標題` 轉為 Emoji 醒目標頭 (如 `📌 標題`)。
        - 將代碼區塊 (```code```) 轉為易讀之縮排卡片格式。
        """
        if not text:
            return ""

        import re
        code_blocks: List[str] = []

        def save_and_format_code_block(match: re.Match) -> str:
            lang = match.group(1).strip()
            code = match.group(2)
            lines = code.splitlines()
            header = f"┌─ 💻 Code ({lang}) ─" if lang else "┌─ 💻 Code ─"
            card_lines = [header]
            for line in lines:
                card_lines.append(f"│ {line}")
            card_lines.append("└──────────────────")
            formatted = "\n".join(card_lines)
            placeholder = f"__CODE_BLOCK_{len(code_blocks)}__"
            code_blocks.append(formatted)
            return placeholder

        # 1. 抽離並格式化代碼區塊，避免代碼內部的 # 被誤判為標題
        pattern = re.compile(r'```(\w*)\n?(.*?)```', re.DOTALL)
        text_with_placeholders = pattern.sub(save_and_format_code_block, text)

        # 2. 轉換標題為 Emoji 醒目標頭
        lines = text_with_placeholders.splitlines()
        formatted_lines: List[str] = []
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith("#### "):
                formatted_lines.append("▪️ " + stripped[5:])
            elif stripped.startswith("### "):
                formatted_lines.append("🔸 " + stripped[4:])
            elif stripped.startswith("## "):
                formatted_lines.append("🔹 " + stripped[3:])
            elif stripped.startswith("# "):
                formatted_lines.append("📌 " + stripped[2:])
            else:
                formatted_lines.append(line)

        result = "\n".join(formatted_lines)

        # 3. 還原並整合代碼區塊卡片
        for i, block in enumerate(code_blocks):
            result = result.replace(f"__CODE_BLOCK_{i}__", block)

        return result

    def deliver_text(self, to_user_id: str, text: str) -> bool:
        """
        深層公開主介面：發送文字訊息。
        對外隱藏 Markdown 格式轉譯適配、2000 字元分段推播與 GUI 桌面發送降級細節。
        """
        formatted_text = self.format_markdown_for_line(text)
        chunks = self.split_text_chunks(formatted_text)
        if not chunks:
            return False

        # 優先嘗試 Messaging API 推播
        if self._messaging_api:
            try:
                for chunk in chunks:
                    push_request = PushMessageRequest(
                        to=to_user_id,
                        messages=[TextMessage(text=chunk)]
                    )
                    self._messaging_api.push_message(push_request)
                logger.info(f"成功透過 Messaging API 發送 {len(chunks)} 段訊息至 {to_user_id}")
                return True
            except Exception as api_err:
                logger.warning(f"Messaging API 推播失敗 ({api_err})，嘗試啟動桌面 GUI 降級發送...")

        # 降級嘗試：macOS 桌面 GUI 自動化發送
        try:
            from app.services.line_desktop_controller import line_desktop_controller
            return line_desktop_controller.send_message(to_user_id, formatted_text)
        except Exception as gui_err:
            logger.error(f"桌面 GUI 降級發送亦失敗: {gui_err}")
            logger.info(f"[模擬發送 Push Message 至 {to_user_id}]: {formatted_text}")
            return False

    def deliver_image(self, to_user_id: str, image_path: str, caption: str = "") -> bool:
        """
        深層公開主介面：發送圖片訊息。
        內部自動處理解析度相容性與桌面 GUI 圖文發送適配。
        """
        # 優先使用桌面 GUI 圖文控制器進行多媒體發送
        try:
            from app.services.line_desktop_controller import line_desktop_controller
            success = line_desktop_controller.send_image(to_user_id, image_path, caption)
            if success:
                logger.info(f"成功發送圖片至使用者: {to_user_id}")
                return True
        except Exception as e:
            logger.warning(f"桌面 GUI 發送圖片失敗: {e}")

        # 若發送失敗，使用文字適配備援
        return self.deliver_text(to_user_id, f"{caption}\n[圖片檔案: {image_path}]")

# 全域單例
line_delivery_adapter = LineDeliveryAdapter()

def format_markdown_for_line(text: str) -> str:
    """模組級輔助函式：調用 line_delivery_adapter.format_markdown_for_line"""
    return line_delivery_adapter.format_markdown_for_line(text)

