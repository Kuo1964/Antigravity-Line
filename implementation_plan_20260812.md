# Candidate 1: AgentSessionEngine 模組深化導入計畫 (2026-08-12)

本計畫旨在針對 **Candidate 1: AgentSessionEngine** 進行代碼深化重構，解決 `app/agent_manager.py` 介面過淺（Shallow Module）與洩漏配置細節的問題。

---

## 🎯 核心目標與原則

1. **高槓桿與深介面 (Deep Module)**：
   將專案檔案樹自動注入 (Workspace Injector)、Gemini API Client 配置、Google Search Grounding 工具動態綁定、對話歷史 Context 壓減等細節徹底隱藏。
2. **極簡呼叫介面 (Interface Simplicity)**：
   Web 路由層 (`app/main.py`) 僅需傳送 `process_user_turn(user_id, prompt)` 即可完成推論與發送。
3. **完整保留歷史規劃**：
   依專案規範，本檔儲存為 `implementation_plan_20260812.md` 以永久保留歷程。

---

## 📂 預計變更檔案 (Proposed Changes)

### 1. 新增 AgentSessionEngine 核心深層模組

#### [NEW] [app/services/agent_session_engine.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/services/agent_session_engine.py)
- 定義 `AgentSessionEngine` 類別。
- 內部聚合 Session Context 管理器、Workspace 檔案樹注入器與 Gemini Grounding Adapter。
- 對外僅提供極簡公開介面：
  - `process_user_turn(user_id: str, prompt: str) -> str`
  - `reset_session(user_id: str) -> bool`
  - `is_busy(user_id: str) -> bool`

### 2. 重構 AgentManager 與 Web 路由層

#### [MODIFY] [app/agent_manager.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/agent_manager.py)
- 改為呼叫 `AgentSessionEngine` 的 Thin Facade，維持向下相容性。

#### [MODIFY] [app/main.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/main.py)
- 更新背景任務調用，直接使用 `AgentSessionEngine`。

### 3. 單元與整合測試

#### [NEW] [tests/test_agent_session_engine.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/tests/test_agent_session_engine.py)
- 撰寫獨立測試，驗證 Context 壓減、Search Grounding 工具開關與任務隔離。

---

## 🧪 驗證計畫 (Verification Plan)

### 自動化測試 (Automated Tests)
- 執行 `./venv/bin/python -m pytest tests/`
- 確保包含 `test_agent_session_engine.py` 在內的所有單元測試全數 100% 通過。

### 手動與功能驗證
- 發送 `/status` 與 `/reset` 指令測試。
- 發送即時新聞查詢 Prompt，驗證 Grounding 搜尋正常運作。
