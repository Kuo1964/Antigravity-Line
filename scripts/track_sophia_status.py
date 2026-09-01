#!/usr/bin/env python3
import os
import sys
import re
from datetime import datetime

PROJECT_ROOT = "/Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line"
LOG_FILE = os.path.join(PROJECT_ROOT, "cron.log")
REPORT_PATH = os.path.join(PROJECT_ROOT, "sophia_track_report.md")

def display_notification(message, title):
    import subprocess
    script = f'display notification "{message}" with title "{title}"'
    try:
        subprocess.run(["osascript", "-e", script], check=False)
    except:
        pass

def main():
    if not os.path.exists(LOG_FILE):
        print(f"找不到日誌檔案: {LOG_FILE}")
        sys.exit(1)

    with open(LOG_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    today_str = datetime.now().strftime("%Y-%m-%d")
    target_header = "=== 啟動正式版早安發送任務 (目標: 'Sophia Kuo') ==="
    
    # Find the most recent run for Sophia Kuo
    start_idx = -1
    for i in range(len(lines)-1, -1, -1):
        if target_header in lines[i]:
            # 檢查日期是否為今天 (或是今晚)
            if today_str in lines[i]:
                start_idx = i
                break

    if start_idx == -1:
        msg = f"尚未在 {LOG_FILE} 找到今天 ({today_str}) 發送給 Sophia Kuo 的紀錄。可能時間還沒到或排程未觸發。"
        print(msg)
        display_notification("等待發送中...", "Sophia 追蹤腳本")
        sys.exit(0)

    # 擷取該次執行的所有 log 直到下一個任務開始
    run_logs = []
    for line in lines[start_idx:]:
        run_logs.append(line.strip())
        # 如果出現另一個任務的開頭，或是執行結束，就不再抓取 (簡單以成功或失敗作為結尾)
        if "🎉 正式發送任務成功" in line or "❌ 正式發送任務失敗" in line:
            break
            
    success = any("🎉 正式發送任務成功" in line for line in run_logs)
    
    report = []
    report.append(f"# 🔍 Sophia 郭 發送狀態追蹤報告")
    report.append(f"**分析時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    if success:
        report.append("> [!SUCCESS]")
        report.append("> 今晚發送給 **Sophia Kuo** 的任務已經 **成功執行完畢**！ ✅")
        display_notification("發送成功！", "Sophia 追蹤報告")
    else:
        report.append("> [!CAUTION]")
        report.append("> 今晚發送給 **Sophia Kuo** 的任務 **執行失敗** ❌")
        display_notification("發送失敗，請查看報告", "Sophia 追蹤報告")
        
    report.append("")
    report.append("## 核心檢測點 (Checkpoint)")
    
    checks = {
        "強制關閉 LINE 重置視窗": "正在關閉 LINE 以重置視窗狀態",
        "重新啟動 LINE": "正在重新啟動 LINE",
        "視窗座標定位": "成功獲取 LINE 視窗座標",
        "點擊全域搜尋框": "原生點擊全域搜尋框座標",
        "鎖定還原機制": "復原 macOS 螢幕狀態至"
    }
    
    report.append("| 檢測項目 | 狀態 |")
    report.append("| :--- | :---: |")
    
    for name, kw in checks.items():
        found = any(kw in line for line in run_logs)
        status = "🟢 成功" if found else "🔴 未觸發/失敗"
        report.append(f"| {name} | {status} |")
        
    report.append("")
    report.append("## 原始執行日誌 (Raw Logs)")
    report.append("```log")
    for log in run_logs:
        report.append(log)
    report.append("```")
    
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
        
    print(f"報告已產出: {REPORT_PATH}")

if __name__ == "__main__":
    main()
