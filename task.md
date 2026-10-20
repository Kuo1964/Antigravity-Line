# 任務清單：啟動 Harness² 技能進行 `.agents` Propose–Probe–Compose 遞迴優化

- [x] 1. 讀取並啟動 `/Users/johnkuo/.gemini/config/skills/harness2/SKILL.md`，檢查本地端 Harness² CLI 環境狀態（`all_clis_ready: true`）
- [x] 2. **Propose 階段**：針對 8 大外圍元件（System Prompt、Guardrails、Memory、Tool Guidance、Subagents、Skills、Scripts、Plugins）提出通用不變性修改與領域特定修改
- [x] 3. 建置 `.agents/` 標準配置目錄與 `harness_manifest.json`，並更新 `AGENT_MEMORY.md` 沉澱四大實證經驗教訓
- [x] 4. **Probe 階段**：
  - [x] 建立自動化探針腳本 `scripts/verify_harness_probe.py` 與單元測試 `tests/test_harness_probe.py`
  - [x] 執行 `harness2-demo` 本地雙層遞迴基準驗證与專案 19 項單元測試
- [x] 5. **Compose 階段**：組合最終 Adopted Harness 配置，提交 Git Commit & Push 並同步更新地端排程目錄 (`/Users/johnkuo/worktemp/Antigravity-Line`)
