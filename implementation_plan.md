# 導入計畫：Harness² 雙層遞迴優化與 `.agents` 8 大外圍元件配置

## 1. 背景與目標 (Background & Objective)
依據 **Google Harness² (Recursive Agent Harnessing for an Open World)** 框架，透過 **Propose–Probe–Compose** 任務層級遞迴與 **Experience Reflector** 編排層級遞迴，將本專案近期解決的四大核心實證教訓（WindowServer Layer >= 1000 鎖屏判定、CLI 缺少 `NSRunLoop` 快取停滯、Accessibility 動態搜尋框回讀、Vision OCR 聊天室標題雙重熔斷）正式結構化至 `.agents/` 的 8 大外圍系統元件中。

---

## 2. Propose–Probe–Compose 雙層遞迴架構

### Phase 1: Propose（提出 8 大元件修改假設）
1. **通用不變性修改 (Invariant Edits)**：
   - **System Prompt** (`.agents/system_prompt.md`)：固化思考優先、最小變更、繁體中文與 Type Hints 規範。
   - **Guardrails** (`.agents/rules/guardrails.md`)：封裝工具呼叫 $\le 8$ 次上限、密碼輸入白名單（`loginwindow`）與 LINE 發送前雙重剛性熔斷閘門。
   - **Tool Guidance** (`.agents/tool_guidance.md`)：規範精準搜尋、禁止盲猜 UI 座標與雲地端雙目錄同步指引。
2. **領域特定修改 (Domain-specific Edits)**：
   - **Memory** (`AGENT_MEMORY.md` & `.agents/memory.md`)：沉澱 macOS 視窗層級、Cocoa `NSRunLoop`、Vision OCR 與雙端同步教訓。
   - **Skills** (`.agents/skills/line-safe-delivery/SKILL.md`)：標準化 6 步安全發送流程。
   - **Scripts** (`scripts/verify_harness_probe.py` & `.agents/scripts/probe_registry.json`)：決定論自動化探針檢測腳本。
   - **Subagents** (`.agents/subagents/macos-ui-auditor.md`)：定義 macOS UI 自動化安全審查子代理。
   - **Plugins** (`.agents/plugins/pre_delivery_check.json`)：定義交付前強制測試與同步檢查 Hook。

### Phase 2: Probe（探針試跑與驗證）
- 執行 `harness2-demo --k 2` 驗證本地端雙層遞迴演算法閉環。
- 執行 `scripts/verify_harness_probe.py` 驗證 `8/8` 元件就緒率、`Quartz`/`AppKit`/`Vision` 框架可用性與全套 19 項單元測試。

### Phase 3: Compose（組合最終配置與雙端同步）
- 產出 `.agents/harness_manifest.json` 收斂 Adopted Harness。
- 推送至 GitHub `main` 並同步更新地端排程目錄 `/Users/johnkuo/worktemp/Antigravity-Line`。
