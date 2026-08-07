#!/usr/bin/env python3
"""
今晚 21:30 發送任務專屬監控與檢驗報告工具 (scripts/tonight_inspector.py)
專門於今晚任務執行完成後 (21:32:00) 自動分析執行細節、LINE 視窗標準化與圖片送達狀況，
並產出可供審核的視覺化 JSON & HTML 報告。
"""

import os
import re
import json
import logging
from datetime import datetime

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CRON_LOG_PATH = os.path.join(PROJECT_DIR, "cron.log")
REPORT_JSON_PATH = os.path.join(PROJECT_DIR, "docs", "tonight_inspection_report_20260807.json")
REPORT_HTML_PATH = os.path.join(PROJECT_DIR, "docs", "tonight_inspection_report_20260807.html")

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def inspect_tonight_execution():
    logger.info("=== 開始分析今晚 21:30 郭泊彤發送任務執行紀錄 ===")
    
    if not os.path.exists(CRON_LOG_PATH):
        logger.error(f"找不到日誌檔案: {CRON_LOG_PATH}")
        return

    with open(CRON_LOG_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    target_lines = []
    target_date_str = datetime.now().strftime("%Y-%m-%d")
    
    for line in lines:
        if f"[{target_date_str} 21:3" in line or f"[{target_date_str} 21:2" in line:
            target_lines.append(line.strip())

    log_text = "\n".join(target_lines)

    # 檢驗指標分析
    check_results = {
        "inspection_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "target": "郭泊彤",
        "cron_triggered": any("啟動正式版早安發送任務 (目標: '郭泊彤')" in l for l in target_lines),
        "wake_unlock_success": any("已完成密碼與 Return 鍵傳送" in l or "跳過輸入密碼步驟" in l for l in target_lines),
        "image_download_success": any("成功下載" in l for l in target_lines),
        "line_focused_bounds": any("Position=(100, 100)" in l or "成功取得 LINE 視窗範圍" in l for l in target_lines),
        "search_and_return_sent": any("原生點擊搜尋結果 '郭泊彤'" in l for l in target_lines),
        "image_pasted_and_sent": any("成功於 LINE 桌面版開啟 '郭泊彤' 並完成早安圖片發送" in l for l in target_lines),
        "overall_status": "SUCCESS" if any("🎉 正式發送任務成功！早安圖片已成功送達 '郭泊彤'！" in l for l in target_lines) else "FAILED",
        "captured_log_entries": target_lines
    }

    # 1. 寫入 JSON 報告
    os.makedirs(os.path.join(PROJECT_DIR, "docs"), exist_ok=True)
    with open(REPORT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(check_results, f, ensure_ascii=False, indent=2)

    # 2. 寫入 HTML 審核報告
    status_color = "#00e676" if check_results["overall_status"] == "SUCCESS" else "#ff1744"
    status_text = "🎉 發送成功 (100% SUCCESS)" if check_results["overall_status"] == "SUCCESS" else "⚠️ 發送失敗 (FAILED)"
    
    logs_html = "".join([f"<li>{l}</li>" for l in target_lines]) if target_lines else "<li>尚無今晚 21:30 的執行紀錄</li>"

    html_content = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <title>今晚 21:30 郭泊彤任務審核報告 ({target_date_str})</title>
    <style>
        body {{ font-family: system-ui, -apple-system, sans-serif; background: #0b0f19; color: #f1f5f9; padding: 2rem; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; background: rgba(22, 31, 49, 0.8); padding: 2rem; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); }}
        h1 {{ color: #00f2fe; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
        .status-banner {{ background: rgba(0,0,0,0.4); padding: 1rem 1.5rem; border-radius: 12px; font-size: 1.25rem; font-weight: bold; color: {status_color}; margin: 1.5rem 0; border: 1px solid {status_color}; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin: 1.5rem 0; }}
        .metric-card {{ background: rgba(255,255,255,0.05); padding: 1rem; border-radius: 10px; border: 1px solid rgba(255,255,255,0.08); }}
        .metric-title {{ font-size: 0.85rem; color: #94a3b8; margin-bottom: 0.25rem; }}
        .metric-val {{ font-size: 1.1rem; font-weight: 600; color: #ffffff; }}
        .log-box {{ background: #050811; padding: 1rem; border-radius: 10px; font-family: monospace; font-size: 0.85rem; color: #38bdf8; max-height: 350px; overflow-y: auto; list-style: none; }}
        .log-box li {{ margin-bottom: 0.3rem; border-bottom: 1px solid rgba(255,255,255,0.03); padding-bottom: 0.2rem; }}
        a {{ color: #00f2fe; text-decoration: none; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <a href="../project_changelog.html" onclick="if (window.opener) {{ window.close(); return false; }}">← 返回專案總覽 (Project Changelog)</a>
        <h1>🌙 今晚 21:30 發送任務監控審核報告</h1>
        <p style="color: #94a3b8;">目標對象：郭泊彤 · 監控時間：{check_results["inspection_time"]}</p>
        
        <div class="status-banner">
            {status_text}
        </div>

        <h3>🔍 核心指標檢查狀態</h3>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-title">Cron 定時啟動</div>
                <div class="metric-val">{"✅ 成功觸發" if check_results["cron_triggered"] else "❌ 未觸發"}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">喚醒與密碼解鎖</div>
                <div class="metric-val">{"✅ 成功解鎖" if check_results["wake_unlock_success"] else "❌ 失敗"}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">網路圖片抓取</div>
                <div class="metric-val">{"✅ 抓取成功" if check_results["image_download_success"] else "❌ 失敗"}</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">LINE 視窗標準化</div>
                <div class="metric-val">{"✅ 標準定位" if check_results["line_focused_bounds"] else "❌ 座標異常"}</div>
            </div>
        </div>

        <h3>📜 今晚實機執行日誌細節 (Captured Logs)</h3>
        <ul class="log-box">
            {logs_html}
        </ul>
    </div>
</body>
</html>'''

    with open(REPORT_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info(f"🎉 監控報告已生成！HTML 檔: {REPORT_HTML_PATH}")

if __name__ == "__main__":
    inspect_tonight_execution()
