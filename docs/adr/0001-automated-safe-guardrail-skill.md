# ADR 0001: 建立全域自動化安全防護 Skill (Safe Guardrail)

## 狀態 (Status)
已接受 (Accepted) - 2026-08-19

## 背景 (Context)
在歷史開發中，使用者為了維護專案穩定性，需手動逐一貼入 4 篇專業角色 Prompt（Reconnaissance ➜ Change-Spec ➜ Code Review ➜ Regression Verification），帶來 8~12 輪的繁瑣確認。

## 決策 (Decision)
1. 將 4 階段防禦流程封裝為全域 Skill：`~/.gemini/config/skills/safe-guardrail/SKILL.md`。
2. 提供 `/safe-apply` 與 `/safe-edit` 命令，由 Agent 在內部自動跑完四階段閉環：
   - 階段 1：Reconnaissance（繪製影響圖，確認受保護模組如早安圖發送器）
   - 階段 2：Change-Spec（定義防破壞約束與測試指標）
   - 階段 3：Code Review（變更前後靜態比對與規格對齊）
   - 階段 4：Regression Verification（沙盒執行 Pytest 與端到端測試）
3. 全程自主驗證，僅在最後輸出一次結構化審查與驗證結果。

## 後果 (Consequences)
- **正面**：單一修復任務的對話輪次從 10~15 輪壓縮至 1~2 輪；所有專案均可受惠。
- **限制**：Skill 需具備足夠的內部引導，確保不跳過嚴格的測試與防破壞約束。
