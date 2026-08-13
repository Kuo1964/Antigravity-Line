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

# 設定 Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(
    title="Antigravity Line Bot Bridge",
    description="連接 Line Messaging API 與本地 Antigravity 2.0 Agent 的雙向控制橋樑",
    version="1.0.0"
)

# 為每個 Line 使用者維護任務 Task Mutex 鎖 (User ID -> asyncio.Lock)
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
    """背景處理 Antigravity Agent 推論並發送 Line Push Message (包含三段式狀態推播與心跳)"""
    lock = get_user_lock(user_id)
    logger.info(f"開始背景執行 Agent 任務 (User: {user_id}, Prompt: '{user_text}')")
    
    # 啟動第二段進度心跳任務 (每 15 秒發送心跳訊息)
    async def heartbeat_loop():
        try:
            while True:
                await asyncio.sleep(15)
                line_delivery_adapter.deliver_text(user_id, "⏳ Agent 仍在執行中，請稍候...")
        except asyncio.CancelledError:
            pass

    heartbeat_task = asyncio.create_task(heartbeat_loop())

    try:
        # 執行 Agent 任務 (內含非阻塞 asyncio.to_thread LLM 呼叫與專案內容注入)
        result_text = await agent_manager.run_agent_task(user_id, user_text)
        
        # 第三段：將最終成果推播給使用者
        line_delivery_adapter.deliver_text(user_id, result_text)
    except Exception as e:
        logger.error(f"背景 Agent 任務執行發生異常: {e}")
        line_delivery_adapter.deliver_text(user_id, f"❌ Agent 執行發生錯誤: {e}")
    finally:
        # 取消心跳任務
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass

        # 釋放使用者的 Mutex Lock
        if lock.locked():
            lock.release()

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
            continue

        # 2. 處理內建控制指令與自然語言專案列表查詢意圖
        if user_text.lower() in ["/reset", "/clear"]:
            agent_manager.reset_session(user_id)
            send_line_push_message(user_id, "🧹 對話、Session 歷史紀錄與專案鎖定已成功重置！")
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
            
            send_line_push_message(user_id, msg)
            continue

        if user_text.lower().startswith("/use "):
            target_name = user_text[5:].strip()
            proj = project_manager.detect_project_from_prompt(target_name)
            if proj:
                agent_manager.set_user_project(user_id, proj)
                send_line_push_message(user_id, f"✅ 已成功將目標專案切換至：【{proj['name']}】\n📁 路徑: {proj['path']}")
            else:
                send_line_push_message(user_id, f"❌ 找不到名稱匹配 '{target_name}' 的專案，請輸入 `/projects` 查看可用專案清單。")
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
            send_line_push_message(user_id, status_msg)
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
            send_line_push_message(user_id, help_msg)
            continue

        # 3. 任務互斥鎖檢查：若上一任務未結束前又發送新指令，推播提示訊息
        lock = get_user_lock(user_id)
        if lock.locked() or agent_manager.is_busy(user_id):
            line_delivery_adapter.deliver_text(user_id, "⚠️ 當前已有執行中的任務，請稍候完成後再下達新指令。")
            continue

        # 獲取 Mutex 鎖以保護背景任務執行
        await lock.acquire()

        try:
            # 確定目標專案名稱
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

            # 第一段推播（秒回 200 OK 告知任務已接收）
            first_stage_msg = f"🚀 已成功接收任務，目標專案 [{proj_name}]，正在背景啟動 Agent 執行..."
            line_delivery_adapter.deliver_text(user_id, first_stage_msg)

            # 4. 一般任務：使用 asyncio.create_task 確保背景協程安全排程並解耦
            asyncio.create_task(process_background_agent_task(user_id, user_text))
        except Exception:
            if lock.locked():
                lock.release()
            raise

    return JSONResponse(content={"status": "ok"}, status_code=200)
