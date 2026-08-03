import pytest
import asyncio
from app.scheduler import send_morning_greeting_job, generate_morning_greeting
from app.config import settings

def test_morning_greeting_generation():
    """驗證早安語錄與圖片生成機制"""
    settings.ALLOWED_USER_IDS = "U_TEST_USER_ID"
    greeting = asyncio.run(generate_morning_greeting())
    assert greeting is not None
    assert len(greeting) > 0

def test_morning_greeting_job_execution():
    """驗證早安圖片推播任務執行流"""
    settings.ALLOWED_USER_IDS = "U_TEST_USER_ID"
    asyncio.run(send_morning_greeting_job())
