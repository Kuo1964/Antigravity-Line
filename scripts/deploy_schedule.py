#!/usr/bin/env python3
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.scheduler_adapter import SchedulerAdapter

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def main():
    project_root = Path(__file__).resolve().parent.parent
    logger.info("============================================================")
    logger.info(" 🚀 開始透過 SchedulerAdapter 佈署 Antigravity Line 排程 ")
    logger.info("============================================================")
    
    # Check if schedule_next_wake.sh is installed in /usr/local/bin
    wake_script_src = project_root / "scripts" / "schedule_next_wake.sh"
    wake_script_dst = Path("/usr/local/bin/schedule_next_wake.sh")
    
    if not wake_script_dst.exists():
        logger.info("安裝 Root 喚醒腳本至 /usr/local/bin/ ...")
        os.system(f"sudo mkdir -p /usr/local/bin")
        os.system(f"sudo cp '{wake_script_src}' '{wake_script_dst}'")
        os.system(f"sudo chmod +x '{wake_script_dst}'")
    
    adapter = SchedulerAdapter(str(project_root))
    adapter.deploy_schedules()
    
    logger.info("============================================================")
    logger.info(" 🎉 排程設定完成！")
    logger.info("▸ 硬體自動喚醒、防睡眠與發送任務皆已透過 Python 統一接管。")
    logger.info("============================================================")

if __name__ == "__main__":
    main()
