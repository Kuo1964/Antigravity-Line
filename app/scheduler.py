import asyncio
import logging
from datetime import datetime, time
from app.config import settings
from app.line_handler import send_line_push_message
from app.agent_manager import agent_manager

logger = logging.getLogger("scheduler")

# 預設每日早安訊息發送時間 (例如 07:00:00)
MORNING_TARGET_TIME = time(7, 0, 0)

async def generate_morning_greeting() -> str:
    """調用 Gemini / Antigravity 生成今天的早安語錄與即時新聞摘要"""
    prompt = "請為我生成一段溫馨勵志的每日早安語錄，並附帶今天天氣與正能量祝福。"
    try:
        # 借用第一位白名單使用者進行對話生成
        first_user = settings.allowed_user_id_list[0] if settings.allowed_user_id_list else "system"
        greeting_text = await agent_manager.run_agent_task(first_user, prompt)
        return greeting_text
    except Exception as e:
        logger.error(f"生成早安訊息失敗: {e}")
        return "☀️ 早上好！新的一天充滿希望與活力，祝您今天順心愉快！"

async def send_morning_greeting_job():
    """廣播推播早安圖片與語錄給所有白名單授權使用者"""
    allowed_users = settings.allowed_user_id_list
    if not allowed_users:
        logger.warning("未設定白名單使用者，跳過早安推播")
        return

    logger.info("⏰ 觸發每日早安自動推播任務！")
    greeting_content = await generate_morning_greeting()
    
    # 搭配優美高畫質早安風景圖片 (Unsplash Source)
    morning_image_url = "https://images.unsplash.com/photo-1470252649378-9c29740c9fa8?auto=format&fit=crop&w=1000&q=80"
    
    msg_body = f"🌅 【Antigravity 每日早安特別推播】\n\n{greeting_content}\n\n🖼️ 每日圖片: {morning_image_url}"

    for user_id in allowed_users:
        send_line_push_message(user_id, msg_body)
        logger.info(f"已發送早安卡片至使用者: {user_id}")

async def start_scheduler_loop():
    """定時排程器迴圈：每日時間觸發檢查"""
    logger.info("早安推播排程器已啟動...")
    while True:
        now = datetime.now()
        # 檢查是否到達目標時間 (例如每日 07:00 附近 1 分鐘內)
        if now.hour == MORNING_TARGET_TIME.hour and now.minute == MORNING_TARGET_TIME.minute:
            logger.info("符合每日早安推播時間，執行發送...")
            await send_morning_greeting_job()
            # 觸發後等待 65 秒避免同分鐘重複觸發
            await asyncio.sleep(65)
        else:
            # 每 30 秒檢查一次時間
            await asyncio.sleep(30)
