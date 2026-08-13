# TICKET-005 實作計畫 (Implementation Plan) - 三段式異步進度心跳推播與任務互斥鎖

## 背景與目標
為提升 LINE 使用者體驗與系統並行執行安全性：
1. **三段式異步狀態推播**：在背景處理耗時 Agent 任務時，實施三段式推播機制：
   - **第一段（秒回 200 OK 時）**：推播 `🚀 已成功接收任務，目標專案 [XXX]，正在背景啟動 Agent 執行...`。
   - **第二段（進度心跳 Progress Heartbeat）**：每 15 秒透過 `line_delivery_adapter.deliver_text` 推播 `⏳ Agent 仍在執行中，請稍候...` 心跳訊息。
   - **第三段（最終成果推播）**：任務完成時推播最終 Agent 成果。
2. **每位 User ID 任務互斥鎖 (`asyncio.Lock`)**：為避免同一使用者連續發送指令導致重複或混亂執行的併發問題，維護全域 `user_locks: Dict[str, asyncio.Lock]`。若上一任務尚未完成又發送新指令，推播 `⚠️ 當前已有執行中的任務，請稍候完成後再下達新指令。`。

## 變更項目

### 1. `app/main.py`
- 新增全域 `user_locks: Dict[str, asyncio.Lock] = {}` 及 `get_user_lock(user_id: str) -> asyncio.Lock`。
- 修改 `/webhook` 端點：
  - 一般任務處理時，先檢視 `lock = get_user_lock(user_id)`。若 `lock.locked()` 或 `agent_manager.is_busy(user_id)`，則透過 `line_delivery_adapter.deliver_text` 推播 `⚠️ 當前已有執行中的任務，請稍候完成後再下達新指令。` 並跳過該事件。
  - 若未鎖定，使用 `await lock.acquire()` 立即獲取鎖。
  - 根據手動鎖定專案、對話動態識別專案或 Session 現狀解析出目標專案名稱 `proj_name`。
  - 推播第一段訊息：`🚀 已成功接收任務，目標專案 [{proj_name}]，正在背景啟動 Agent 執行...`。
  - 安排 `background_tasks.add_task(process_background_agent_task, user_id, user_text)`。
- 修改 `process_background_agent_task(user_id: str, user_text: str)`：
  - 建立背景心跳 task（每 15 秒推播 `⏳ Agent 仍在執行中，請稍候...`）。
  - 呼叫 `await agent_manager.run_agent_task(user_id, user_text)` 取得成果。
  - 推播第三段成果訊息。
  - 於 `finally` 區塊中：
    - 取消心跳 task。
    - 釋放使用者任務鎖：`if lock.locked(): lock.release()`。

### 2. `tests/test_webhook.py`
- 新增 `test_three_stage_async_push()` 驗證第一段接收推播、第二段心跳推播與第三段成果推播流程。
- 新增 `test_user_task_mutex_lock()` 驗證重複發送指令時正確推播互斥提示訊息 `⚠️ 當前已有執行中的任務，請稍候完成後再下達新指令。`。

## 驗證流程
- 執行 `./venv/bin/python -m pytest tests/test_webhook.py` 確保 100% 綠燈通過。
