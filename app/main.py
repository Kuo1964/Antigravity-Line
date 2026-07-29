import logging
from fastapi import FastAPI, Request, HTTPException, Header, BackgroundTasks
from fastapi.responses import JSONResponse
from app.config import settings
from app.agent_manager import agent_manager
from app.line_handler import send_line_push_message

# 設定 Logging 格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")

app = FastAPI(
    title="Antigravity Line Bot Bridge",
    description="透過 Line Bot 雙向控制 Antigravity Agent 的 Webhook 服務",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """健康檢查端點"""
    return {"status": "ok", "service": "Antigravity Line Bot Bridge"}

async def process_background_agent_task(user_id: str, user_text: str):
    """背景處理 Antigravity Agent 推論並發送 Line Push Message"""
    logger.info(f"開始背景執行 Agent 任務 (User: {user_id}, Prompt: '{user_text}')")
    
    # 執行 Agent 任務
    result_text = await agent_manager.run_agent_task(user_id, user_text)
    
    # 將推論與執行成果推播給使用者
    send_line_push_message(user_id, result_text)

@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature: str = Header(None)
):
    """Line Webhook 主處理端點"""
    body_bytes = await request.body()
    body_json = await request.json()
    
    events = body_json.get("events", [])
    if not events:
        return JSONResponse(content={"status": "no events"}, status_code=200)

    for event in events:
        # 僅處理文字訊息事件
        if event.get("type") != "message" or event.get("message", {}).get("type") != "text":
            continue

        user_id = event.get("source", {}).get("userId")
        user_text = event.get("message", {}).get("text", "").strip()

        if not user_id:
            continue

        # 1. 存取權限驗證：檢查 Line User ID 是否在白名單內
        if not settings.is_user_allowed(user_id):
            logger.warning(f"拒絕未授權的使用者存取: {user_id}")
            # 為保護伺服器不主動推播干擾，僅記錄 log
            continue

        # 2. 處理內建控制指令
        if user_text.lower() in ["/reset", "/clear"]:
            agent_manager.reset_session(user_id)
            send_line_push_message(user_id, "🧹 對話與 Session 歷史紀錄已成功重置！")
            continue

        if user_text.lower() == "/status":
            is_busy = agent_manager.is_busy(user_id)
            status_msg = "⚙️ 系統狀態報告：\n"
            status_msg += f"- 當前連線使用者: {user_id}\n"
            status_msg += f"- Agent 狀態: {'⏳ 執行任務中' if is_busy else '✅ 待命狀態 (Idle)'}"
            send_line_push_message(user_id, status_msg)
            continue

        if user_text.lower() == "/help":
            help_msg = (
                "🤖 【Antigravity Line 控制指令手冊】\n\n"
                "• 直接輸入任何文字 Prompt 即可觸發 Antigravity Agent 執行任務。\n"
                "• /status  : 查詢目前 Agent 執行狀態\n"
                "• /reset   : 清除並重置過去對話 Session 上下文\n"
                "• /help    : 顯示此說明選單"
            )
            send_line_push_message(user_id, help_msg)
            continue

        # 3. 若 Agent 正在處理該使用者的上一筆任務，給予提示
        if agent_manager.is_busy(user_id):
            send_line_push_message(user_id, "⚠️ 當前尚有執行中的任務，請稍候任務完成後再下達新指令。")
            continue

        # 4. 一般任務：安排 FastAPI 背景任務異步處理，並立即回應 200 OK
        background_tasks.add_task(process_background_agent_task, user_id, user_text)

    return JSONResponse(content={"status": "ok"}, status_code=200)
