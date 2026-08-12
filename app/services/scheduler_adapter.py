import json
import logging
import os
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

MARKER_START = "# --- Antigravity Line START ---"
MARKER_END = "# --- Antigravity Line END ---"

class SchedulerAdapter:
    """
    Adapter for managing macOS pmset and crontab schedules.
    Encapsulates the generation and deployment of scheduling rules.
    """
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.config_path = self.project_root / "app" / "config" / "schedule_tasks.json"

    def load_tasks(self) -> list[dict]:
        """讀取排程設定檔"""
        if not self.config_path.exists():
            logger.warning(f"設定檔 {self.config_path} 不存在")
            return []
        
        with open(self.config_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _replace_crontab_block(self, current_cron: str, new_block: str) -> str:
        """安全替換被 Marker 包夾的 cron 區塊"""
        lines = current_cron.splitlines()
        new_lines = []
        in_block = False
        
        for line in lines:
            if line.strip() == MARKER_START:
                in_block = True
                continue
            if line.strip() == MARKER_END:
                in_block = False
                continue
            if not in_block:
                new_lines.append(line)
        
        # 過濾掉結尾多餘的空行
        while new_lines and not new_lines[-1].strip():
            new_lines.pop()

        if new_block.strip():
            new_lines.append(MARKER_START)
            new_lines.append(new_block.strip())
            new_lines.append(MARKER_END)
            
        return "\n".join(new_lines) + "\n"

    def _deploy_cron(self, cron_content: str, use_sudo: bool = False):
        """實際寫入 crontab"""
        cmd = ["sudo", "crontab", "-"] if use_sudo else ["crontab", "-"]
        try:
            process = subprocess.run(
                cmd, 
                input=cron_content, 
                text=True, 
                check=True,
                capture_output=True
            )
            logger.info("Crontab 佈署成功")
        except subprocess.CalledProcessError as e:
            logger.error(f"Crontab 佈署失敗: {e.stderr}")
            raise

    def deploy_schedules(self):
        """讀取設定並佈署 User 與 Root 的 crontab"""
        tasks = self.load_tasks()
        if not tasks:
            logger.error("沒有找到任何排程設定！")
            return

        user_cron_lines = []
        root_cron_lines = []

        for task in tasks:
            target = task.get("target")
            send_time = task.get("send_time")
            wake_time = task.get("wake_time")
            
            if not (target and send_time and wake_time):
                logger.warning(f"略過格式錯誤的排程: {task}")
                continue

            # Parse times (HH:MM)
            try:
                sh, sm = map(int, send_time.split(':'))
                wh, wm = map(int, wake_time.split(':'))
            except ValueError:
                logger.warning(f"時間格式錯誤 (需為 HH:MM): {send_time}, {wake_time}")
                continue
                
            # Caffeinate needs to run 2 mins before send_time
            # For simplicity, we just use the wake_time (since wake_time is exactly 2 mins before send_time in current setup)
            # Or we calculate it, but let's just use wake_time minutes and hour.
            # E.g. wake_time "08:58" -> caffeinate at 08:58
            ch, cm = wh, wm

            # User Cron: Caffeinate + Send Script
            user_cron_lines.append(f"{cm} {ch} * * * /usr/bin/caffeinate -u -t 300")
            user_cron_lines.append(
                f"{sm} {sh} * * * cd \"{self.project_root}\" && PYTHONPATH=. ./venv/bin/python scripts/send_daily_morning_card.py --target \"{target}\" --countdown 1 >> \"{self.project_root}/cron.log\" 2>&1"
            )

            # Root Cron: schedule_next_wake.sh (Wait, the root cron actually schedules the NEXT wake)
            # The original logic: 09:05 sets wake for 21:28, 21:35 sets wake for 08:58
            # To generalize, we just schedule the wake time of the NEXT task, 5 mins after CURRENT task.
            pass

        # Since the original root logic was specifically: 
        # "5 9 * * * /usr/local/bin/schedule_next_wake.sh 21:28:00"
        # "35 21 * * * /usr/local/bin/schedule_next_wake.sh 08:58:00"
        # We can calculate the next task's wake time dynamically.
        
        # Sort tasks by time
        tasks_sorted = sorted(tasks, key=lambda x: x["send_time"])
        for i, task in enumerate(tasks_sorted):
            curr_sh, curr_sm = map(int, task["send_time"].split(':'))
            next_task = tasks_sorted[(i + 1) % len(tasks_sorted)]
            next_wake = next_task["wake_time"] + ":00"
            
            # Root cron runs 5 mins after send_time
            trigger_m = (curr_sm + 5) % 60
            trigger_h = curr_sh + ((curr_sm + 5) // 60)
            
            root_cron_lines.append(
                f"{trigger_m} {trigger_h} * * * /usr/local/bin/schedule_next_wake.sh {next_wake} >> \"{self.project_root}/temp/cron_wake.log\" 2>&1"
            )
            
        user_block = "\n".join(user_cron_lines)
        root_block = "\n".join(root_cron_lines)

        # Deploy User Crontab
        try:
            curr_user_cron = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
        except:
            curr_user_cron = ""
            
        new_user_cron = self._replace_crontab_block(curr_user_cron, user_block)
        self._deploy_cron(new_user_cron, use_sudo=False)
        logger.info("使用者 Crontab 佈署完成")

        # Deploy Root Crontab
        try:
            curr_root_cron = subprocess.run(["sudo", "crontab", "-l"], capture_output=True, text=True).stdout
        except:
            curr_root_cron = ""
            
        new_root_cron = self._replace_crontab_block(curr_root_cron, root_block)
        self._deploy_cron(new_root_cron, use_sudo=True)
        logger.info("Root Crontab (Wake Relay) 佈署完成")

        # Initial PMSet kick-off (Set the next closest wake time)
        # For simplicity, we just trigger the root script for the first task's wake time right now.
        first_wake = tasks_sorted[0]["wake_time"] + ":00"
        subprocess.run(["sudo", "pmset", "repeat", "cancel"], check=False)
        subprocess.run(["sudo", "/usr/local/bin/schedule_next_wake.sh", first_wake], check=False)
        
        logger.info("已設定初始喚醒排程")
