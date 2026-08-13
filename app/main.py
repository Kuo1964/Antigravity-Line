import os
import asyncio
import logging
from typing import Dict
from fastapi import FastAPI, Request, Header, BackgroundTasks, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.project_manager import project_manager
from app.agent_manager import agent_manager
from app.services.line_delivery_adapter import line_delivery_adapter
from app.services.execution_tracer import execution_tracer

# 設定 Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(
    title="Antigravity Line Bot Bridge",
    description="連接 Line Messaging API 與本地 Antigravity 2.0 Agent 的雙向控制橋樑",
    version="1.0.0"
)

user_locks: Dict[str, asyncio.Lock] = {}

def get_user_lock(user_id: str) -> asyncio.Lock:
    """取得或建立使用者的 asyncio.Lock」"""
    if user_id not in user_locks:
        user_locks[user_id] = asyncio.Lock()
    return user_locks[user_id]

def send_line_push_message(to_user_id: str, text: str) -> bool:
    """公開導出介面：調用 LineDeliveryAdapter 發送 Push Message」"""
    return line_delivery_adapter.deliver_text(to_user_id, text)

@app.get("/health")
async def health_check():
    """系統健康檢查端點"""
    return {"status": "ok", "service": "Antigravity Line Bot Bridge"}

async def process_background_agent_task(user_id: str, user_text: str):
    """背景處理 Antigravity Agent 推論並發送 Line Push Message (包含三段式狀態推播、心跳與 90s 非阻塞保護)"""
    lock = get_user_lock(user_id)
    execution_tracer.log_event("BACKGROUND_TASK_START", {
        "user_id": user_id,
        "user_text": user_text
    })
    logger.info(f"開始背景執行 Agent 任務 (User: {user_id}, Prompt: '{user_text}')")
    
    async def heartbeat_loop():
        try:
            while True:
                await asyncio.sleep(15)
                execution_tracer.log_event("HEARTBEAT_TRIGGERED", {"user_id": user_id})
                line_delivery_adapter.deliver_text(user_id, "⏳ Agent 仍在執行中，請稍候...")
        except asyncio.CancelledError:
            pass

    heartbeat_task = asyncio.create_task(heartbeat_loop())

    try:
        # 擴充為 90 秒最大超時防禦
        result_text = await asyncio.wait_for(
            agent_manager.run_agent_task(user_id, user_text),
            timeout=90.0
        )
        
        execution_tracer.log_event("AGENT_TASK_COMPLETED", {
            "user_id": user_id,
            "result_length": len(result_text) if result_text else 0,
            "result_preview": result_text[:150] if result_text else ""
        })

        line_delivery_adapter.deliver_text(user_id, result_text)

    except asyncio.TimeoutError:
        execution_tracer.log_event("AGENT_TASK_TIMEOUT", {"user_id": user_id, "timeout": 90.0})
        logger.error(f"背景 Agent 任務超時 (90s): User {user_id}")
        line_delivery_adapter.deliver_text(user_id, "⚠️ 任務執行耗時過長已超時降級，請重新發送或嘗試縮短指令內容。")
    except Exception as e:
        execution_tracer.log_event("AGENT_TASK_EXCEPTION", {"user_id": user_id, "error": str(e)})
        logger.error(f"背景 Agent 任務執行發生異常: {e}")
        line_delivery_adapter.deliver_text(user_id, f"❌ Agent 執行發生錯誤: {e}")
    finally:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

        if lock.locked():
            lock.release()
            execution_tracer.log_event("MUTEX_LOCK_RELEASED", {"user_id": user_id})

@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_line_signature: str = Header(None)
):
    """Line Webhook 主處理端點"""
    body_json = await request.json()
    
    events = body_json.get("events", [])
    if not events:
        return JSONResponse(content={"status": "no events"}, status_code=200)

    for event in events:
        if event.get("type") != "message" or event.get("message", {}).get("type") != "text":
            continue

        user_id = event.get("source", {}).get("userId")
        user_text = event.get("message", {}).get("text", "").strip()

        if not user_id:
            continue

        execution_tracer.log_event("WEBHOOK_RECEIVED", {
            "user_id": user_id,
            "user_text": user_text,
            "replyToken": event.get("replyToken")
        })

        if not settings.is_user_allowed(user_id):
            execution_tracer.log_event("USER_UNAUTHORIZED", {"user_id": user_id})
            logger.warning(f"拒絕未授權的使用者存取: {user_id}")
            continue

        if user_text.lower() in ["/reset", "/clear"]:
            agent_manager.reset_session(user_id)
            line_delivery_adapter.deliver_text(user_id, "🧹 對話、Session 歷史紀錄與專案鎖定已成功重置！")
            continue

        is_project_list_intent = (
            user_text.lower() in ["/projects", "/ps"] or
            any(kw in user_text for kw in ["有哪些專案", "專案清單", "專案列表", "專案有哪些", "所有專案", "進行中的專案", "專案正在進行"])
        )
        if is_project_list_intent:
            projects = project_manager.list_projects()
            session = agent_manager.get_or_create_session(user_id)
            curr = session.get("current_project")
            curr_name = curr["name"] if curr else "（未指定，預設搜尋全工作區）"

            msg = "📂 【工作區專案列表】\n"
            msg += f"📍 當前鎖定專案: {curr_name}\n\n"
            if not projects:
                msg += "⚠️ 目前工作區下未掃描到任何專案資料夾。"
            else:
                msg += f"共掃描到 {len(projects)} 個專案：\n"
                for idx, p in enumerate(projects, 1):
                    prefix = "👉 " if (curr and curr["name"] == p["name"]) else "• "
                    msg += f"{prefix}{idx}. {p['name']}\n"
                msg += "\n💡 提示：在對話中直接輸入專案名稱（如「在 Antigravity-Line 執行測試」）或使用 `/use <專案名>` 即可自動切換！"
            
            line_delivery_adapter.deliver_text(user_id, msg)
            continue

        if user_text.lower().startswith("/use "):
            target_name = user_text[5:].strip()
            proj = project_manager.detect_project_from_prompt(target_name)
            if proj:
                agent_manager.set_user_project(user_id, proj)
                line_delivery_adapter.deliver_text(user_id, f"✅ 已成功將目標專案切換至：【{proj['name']}】\n📁 路徑: {proj['path']}")
            else:
                line_delivery_adapter.deliver_text(user_id, f"❌ 找不到名稱匹配 '{target_name}' 的專案，請輸入 `/projects` 查看可用專案清單。")
            continue

        if user_text.lower() == "/status":
            is_busy = agent_manager.is_busy(user_id)
            session = agent_manager.get_or_create_session(user_id)
            curr_proj = session.get("current_project")
            curr_proj_str = f"{curr_proj['name']} ({curr_proj['path']})" if curr_proj else "全工作區 (未鎖定)"
            
            status_msg = "⚙️ 系統狀態報告：\n"
            status_msg += f"- 連線使用者: {user_id}\n"
            status_msg += f"- 目標專案: {curr_proj_str}\n"
            status_msg += f"- Agent 狀態: {'⏳ 執行任務中' if is_busy else '✅ 待命狀態 (Idle)'}"
            line_delivery_adapter.deliver_text(user_id, status_msg)
            continue

        if user_text.lower() == "/help":
            help_msg = (
                "🤖 【Antigravity Line 多專案控制指令手冊】\n\n"
                "• 直接輸入對話或帶有專案名稱之指令（如「幫我在 Antigravity-Line 跑測試」）即可觸發控制。\n"
                "• /projects (或 /ps) : 列出工作區所有專案及當前鎖定項目\n"
                "• /use <專案名>      : 手動切換當前鎖定的目標專案\n"
                "• /status            : 查詢目前 Agent 執行狀態與專案資訊\n"
                "• /reset             : 清除並重置對話與專案 Session\n"
                "• /help              : 顯示此說明選單"
            )
            line_delivery_adapter.deliver_text(user_id, help_msg)
            continue

        lock = get_user_lock(user_id)
        if lock.locked() or agent_manager.is_busy(user_id):
            execution_tracer.log_event("USER_LOCK_MUTEX_BLOCKED", {"user_id": user_id})
            line_delivery_adapter.deliver_text(user_id, "⚠️ 當前已有執行中的任務，請稍候完成後再下達新指令。")
            continue

        await lock.acquire()
        execution_tracer.log_event("MUTEX_LOCK_ACQUIRED", {"user_id": user_id})

        try:
            user_proj = agent_manager.get_user_project(user_id)
            detected_proj = project_manager.detect_project_from_prompt(user_text)
            session = agent_manager.get_or_create_session(user_id)
            curr_proj = session.get("current_project")

            if user_proj and user_proj.get("name"):
                proj_name = user_proj["name"]
            elif detected_proj and detected_proj.get("name"):
                proj_name = detected_proj["name"]
            elif curr_proj and curr_proj.get("name"):
                proj_name = curr_proj["name"]
            else:
                proj_name = "全工作區"

            first_stage_msg = f"🚀 已成功接收任務，目標專案 [{proj_name}]，正在背景啟動 Agent 執行..."
            line_delivery_adapter.deliver_text(user_id, first_stage_msg)

            asyncio.create_task(process_background_agent_task(user_id, user_text))
        except Exception as err:
            execution_tracer.log_event("FIRST_STAGE_EXCEPTION", {"error": str(err)})
            if lock.locked():
                lock.release()
            raise

    return JSONResponse(content={"status": "ok"}, status_code=200)
