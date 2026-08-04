#!/usr/bin/env python3
"""
專案 HTML 開發歷程與變更紀錄自動更新工具 (scripts/update_changelog.py)
支援自動建立帶有日期編號的 Implementation Plan 與 Walkthrough 專屬超連結
"""

import os
import re
import sys
import shutil
import argparse
from datetime import datetime

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHANGELOG_PATH = os.path.join(PROJECT_DIR, "project_changelog.html")
DOCS_DIR = os.path.join(PROJECT_DIR, "docs")
PLANS_DIR = os.path.join(DOCS_DIR, "plans")
WALKTHROUGHS_DIR = os.path.join(DOCS_DIR, "walkthroughs")

def ensure_dirs():
    os.makedirs(PLANS_DIR, exist_ok=True)
    os.makedirs(WALKTHROUGHS_DIR, exist_ok=True)

def append_changelog_entry(title: str, entry_type: str, desc: str, details: list[str], plan_file: str = None, walkthrough_file: str = None) -> bool:
    ensure_dirs()
    if not os.path.exists(CHANGELOG_PATH):
        print(f"錯誤：找不到 {CHANGELOG_PATH}")
        return False

    with open(CHANGELOG_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    items = re.findall(r'<div class="timeline-item">', content)
    item_num = len(items) + 1
    date_code = datetime.now().strftime("%Y%m%d")
    date_display = datetime.now().strftime("%Y-%m-%d")

    badge_class = "badge-feat"
    dot_class = ""
    if entry_type.lower() == "fix":
        badge_class = "badge-fix"
        dot_class = "warning"
    elif entry_type.lower() in ["verify", "docs"]:
        badge_class = "badge-verify"
        dot_class = "success"

    # 處理 Plan 與 Walkthrough 專屬連結
    links_html = ""
    if plan_file and os.path.exists(plan_file):
        dest_plan = os.path.join(PLANS_DIR, f"plan_{date_code}_v{item_num}.html")
        shutil.copy(plan_file, dest_plan)
        rel_plan = f"docs/plans/plan_{date_code}_v{item_num}.html"
        links_html += f'<a href="{rel_plan}" target="_blank" class="btn-link btn-plan" style="font-size: 0.8rem; padding: 0.3rem 0.75rem; margin-top: 0.5rem; margin-right: 0.5rem;">📄 Plan ({date_display})</a>'

    if walkthrough_file and os.path.exists(walkthrough_file):
        dest_wt = os.path.join(WALKTHROUGHS_DIR, f"walkthrough_{date_code}_v{item_num}.html")
        shutil.copy(walkthrough_file, dest_wt)
        rel_wt = f"docs/walkthroughs/walkthrough_{date_code}_v{item_num}.html"
        links_html += f'<a href="{rel_wt}" target="_blank" class="btn-link btn-walkthrough" style="font-size: 0.8rem; padding: 0.3rem 0.75rem; margin-top: 0.5rem;">🧪 Walkthrough ({date_display})</a>'

    links_wrapper = f'<div style="margin-top: 0.75rem;">{links_html}</div>' if links_html else ""

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
                    {links_wrapper}
                </div>
            </div>
'''

    timeline_tag = '<div class="timeline" id="changelog-timeline">'
    if timeline_tag in content:
        content = content.replace(timeline_tag, timeline_tag + new_entry_html)
    else:
        print("錯誤：找不到 timeline 標籤")
        return False

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    content = re.sub(r'<span id="update-time">.*?</span>', f'<span id="update-time">{now_str}</span>', content)

    with open(CHANGELOG_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"🎉 成功更新 project_changelog.html (新增變動 #{item_num}: {title})")
    return True

def main():
    parser = argparse.ArgumentParser(description="自動更新 project_changelog.html 歷程")
    parser.add_argument("--title", required=True, help="變更標題")
    parser.add_argument("--type", default="feat", choices=["feat", "fix", "verify", "docs"], help="類別")
    parser.add_argument("--desc", default="", help="簡短描述")
    parser.add_argument("--details", nargs="+", default=[], help="詳細變更點")
    parser.add_argument("--plan-file", default=None, help="Implementation Plan HTML/MD 檔路徑")
    parser.add_argument("--walkthrough-file", default=None, help="Walkthrough HTML/MD 檔路徑")
    args = parser.parse_args()

    append_changelog_entry(args.title, args.type, args.desc, args.details, args.plan_file, args.walkthrough_file)


if __name__ == "__main__":
    main()
