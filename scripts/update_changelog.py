#!/usr/bin/env python3
"""
專案 HTML 開發歷程與變更紀錄自動更新工具 (scripts/update_changelog.py)
"""

import os
import re
import sys
import argparse
from datetime import datetime

CHANGELOG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "project_changelog.html"))

def append_changelog_entry(title: str, entry_type: str, desc: str, details: list[str]) -> bool:
    if not os.path.exists(CHANGELOG_PATH):
        print(f"錯誤：找不到 {CHANGELOG_PATH}")
        return False

    with open(CHANGELOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 計算目前的條數
    items = re.findall(r'<div class="timeline-item">', content)
    item_num = len(items) + 1

    badge_class = "badge-feat"
    dot_class = ""
    if entry_type.lower() == "fix":
        badge_class = "badge-fix"
        dot_class = "warning"
    elif entry_type.lower() in ["verify", "docs"]:
        badge_class = "badge-verify"
        dot_class = "success"

    details_html = "".join([f"<li>{d}</li>" for d in details])

    new_entry_html = f'''
            <!-- 變動 {item_num} -->
            <div class="timeline-item">
                <div class="timeline-dot {dot_class}"></div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <span class="timeline-title">{item_num}. {title}</span>
                        <span class="badge {badge_class}">{entry_type.upper()}</span>
                    </div>
                    <p class="timeline-desc">{desc}</p>
                    <ul class="timeline-list">
                        {details_html}
                    </ul>
                </div>
            </div>
'''

    # 將新條目插入到 <div class="timeline" id="changelog-timeline"> 標籤後
    timeline_tag = '<div class="timeline" id="changelog-timeline">'
    if timeline_tag in content:
        content = content.replace(timeline_tag, timeline_tag + new_entry_html)
    else:
        print("錯誤：找不到 timeline 標籤")
        return False

    # 更新頁腳時間
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = re.sub(r'<span id="update-time">.*?</span>', f'<span id="update-time">{now_str}</span>', content)

    with open(CHANGELOG_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"🎉 成功更新 project_changelog.html (新增紀錄: {title})")
    return True

def main():
    parser = argparse.ArgumentParser(description="自動更新 project_changelog.html 歷程")
    parser.add_argument("--title", required=True, help="變更標題")
    parser.add_argument("--type", default="feat", choices=["feat", "fix", "verify", "docs"], help="類別 (feat, fix, verify, docs)")
    parser.add_argument("--desc", default="", help="簡短描述")
    parser.add_argument("--details", nargs="+", default=[], help="詳細變更點清單")
    args = parser.parse_args()

    append_changelog_entry(args.title, args.type, args.desc, args.details)

if __name__ == "__main__":
    main()
