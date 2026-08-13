import os
import time
import json
import logging
from typing import Any, Dict

TRACE_LOG_PATH = os.path.join(os.getcwd(), "app", "data", "execution_trace.log")

class ExecutionTracer:
    """
    實時執行追蹤器：專門紀錄從 LINE 接收任務、背景 Agent 推論到 LINE API 推播的完整生命週期
    """
    def __init__(self, log_path: str = TRACE_LOG_PATH):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    def log_event(self, stage: str, details: Dict[str, Any]):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        log_entry = {
            "timestamp": timestamp,
            "stage": stage,
            "details": details
        }
        formatted_str = f"[{timestamp}] [{stage}]\n{json.dumps(details, ensure_ascii=False, indent=2)}\n" + ("─"*60) + "\n"
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(formatted_str)
            print(formatted_str)
        except Exception as e:
            logging.error(f"寫入追蹤日誌失敗: {e}")

    def clear_trace(self):
        try:
            with open(self.log_path, "w", encoding="utf-8") as f:
                f.write(f"=== 執行追蹤日誌初始化 ({time.strftime('%Y-%m-%d %H:%M:%S')}) ===\n\n")
        except Exception:
            pass

execution_tracer = ExecutionTracer()
