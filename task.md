# TICKET-005: 三段式異步進度心跳推播與任務互斥鎖

## 任務清單
- [x] 撰寫實作計畫 `implementation_plan.md` <!-- id: 0 -->
- [x] 在 `app/main.py` 與 `process_background_agent_task` 實現三段式異步狀態推播與任務互斥鎖 <!-- id: 1 -->
  - [x] 每位 LINE `user_id` 維護任務互斥鎖 (`asyncio.Lock`)，若上一任務未結束又下達新指令，推播 `「⚠️ 當前已有執行中的任務，請稍候完成後再下達新指令。」` <!-- id: 2 -->
  - [x] 第一段推播（秒回 200 OK）：`「🚀 已成功接收任務，目標專案 [XXX]，正在背景啟動 Agent 執行...」` <!-- id: 3 -->
  - [x] 第二段推播（進度心跳）：長任務每 15 秒透過 `line_delivery_adapter.deliver_text` 推播 `「⏳ Agent 仍在執行中，請稍候...」` 心跳訊息 <!-- id: 4 -->
  - [x] 第三段推播：最終成果推播 `result_text` <!-- id: 5 -->
- [x] 更新/撰寫 `tests/test_webhook.py` 測試案例 <!-- id: 6 -->
- [x] 執行 `./venv/bin/python -m pytest tests/test_webhook.py` 確保 100% 綠燈通過 <!-- id: 7 -->
- [x] 回報實作細節與測試驗證結果至 Parent Agent <!-- id: 8 -->
