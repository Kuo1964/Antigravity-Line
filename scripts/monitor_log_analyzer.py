#!/usr/bin/env python3
import os
import re
import sys
from datetime import datetime
import subprocess

PROJECT_ROOT = "/Users/johnkuo/worktemp/Antigravity-Line"
LOG_FILE = os.path.join(PROJECT_ROOT, "cron.log")
REPORT_DIR = "/tmp/morning_images"

def display_notification(message, title):
    script = f'display notification "{message}" with title "{title}"'
    try:
        subprocess.run(["osascript", "-e", script], check=False)
    except Exception as e:
        print(f"Notification failed: {e}")

def main():
    if not os.path.exists(LOG_FILE):
        print(f"Log file not found: {LOG_FILE}")
        sys.exit(1)

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the last task start
    start_idx = -1
    for i in range(len(lines)-1, -1, -1):
        if "=== 啟動正式版早安發送任務" in lines[i]:
            start_idx = i
            break

    if start_idx == -1:
        print("No task run found in log.")
        sys.exit(1)

    latest_run = lines[start_idx:]
    
    # Analyze components
    report = []
    report.append(f"# 📅 LINE 自動發送監控報告 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
    report.append("")
    report.append("## 執行狀態摘要 (Execution Summary)")
    
    success = any("正式發送任務成功！" in line for line in latest_run)
    if success:
        report.append("> [!SUCCESS]")
        report.append("> 今晚發送任務 **執行成功**！✅")
    else:
        report.append("> [!CAUTION]")
        report.append("> 今晚發送任務 **執行失敗**！❌")
        
    report.append("")
    report.append("## 關鍵節點檢查 (Health Checks)")
    
    checks = {
        "Mac 螢幕喚醒": ("macOS 螢幕處於開啟用戶端狀態，系統準備完畢", "發送喚醒訊號 (caffeinate)"),
        "早安圖抓取": ("成功下載網路搜尋到的中文早安圖", "成功下載並快取早安圖片至"),
        "圖片存入剪貼簿": ("圖片已成功寫入 macOS 系統剪貼簿", "準備寫入圖片至剪貼簿"),
        "LINE 視窗喚醒 (open -a)": ("正在透過 macOS 原生指令強制展開/喚醒: LINE",),
        "LINE 視窗座標獲取": ("成功獲取 LINE 視窗座標",),
        "成功發送與還原鎖定": ("復原 macOS 螢幕狀態至", "已成功恢復發送前狀態：Mac 顯示器已重新睡眠並鎖定")
    }

    report.append("| 檢查項目 | 狀態 | 備註 |")
    report.append("| :--- | :---: | :--- |")
    
    for check_name, keywords in checks.items():
        found = False
        detail = ""
        for line in latest_run:
            if any(kw in line for kw in keywords):
                found = True
                # Extract time and brief content
                match = re.search(r'\[(.*?)\] (.*)', line.strip())
                if match:
                    detail = match.group(2)[:40] + "..."
                break
        
        status_icon = "🟢 OK" if found else "🔴 FAIL"
        report.append(f"| {check_name} | {status_icon} | {detail} |")

    report.append("")
    report.append("## 詳細錯誤日誌 (Error Logs)")
    
    errors = [line.strip() for line in latest_run if "[ERROR]" in line or "[WARNING]" in line]
    if errors:
        report.append("```log")
        for err in errors:
            report.append(err)
        report.append("```")
    else:
        report.append("_本次執行無任何錯誤或警告。_")

    os.makedirs(REPORT_DIR, exist_ok=True)
    report_path = os.path.join(REPORT_DIR, f"monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print(f"Report generated: {report_path}")
    
    msg = "發送成功 ✅" if success else "發送失敗 ❌，請檢查報告"
    display_notification(msg, "LINE 自動發送監控")

if __name__ == "__main__":
    main()
