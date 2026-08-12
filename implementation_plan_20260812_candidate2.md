# Candidate 2: LineDeliveryAdapter 模組深化導入計畫 (2026-08-12)

本計畫旨在針對 **Candidate 2: LineDeliveryAdapter** 進行代碼深化重構，解決 Messaging API (`app/line_handler.py`) 與 macOS 桌面 GUI 發送 (`line_desktop_controller.py`) 發送邏輯分散、介面洩漏 (Leaky Dispatch) 的問題。

---

## 🎯 核心目標與原則

1. **高槓桿與深介面 (Deep Module)**：
   將長訊息 2000 字元切割邏輯、API 失敗時的桌面 GUI 自動化降級發送、以及發送日誌記錄徹底隱藏。
2. **統一發送介面 (Interface Simplicity)**：
   呼叫端（如 `main.py` 與 `scheduler.py`）僅需傳送 `deliver_text(to_user_id, text)` 或 `deliver_image(to_user_id, image_path)`。
3. **完整保留歷史規劃**：
   依專案規範，本檔儲存為 `implementation_plan_20260812_candidate2.md` 以永久保留歷程。

---

## 📂 預計變更檔案 (Proposed Changes)

### 1. 新增 LineDeliveryAdapter 核心深層適配器

#### [NEW] [app/services/line_delivery_adapter.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/services/line_delivery_adapter.py)
- 定義 `LineDeliveryAdapter` 類別。
- 內部整合 Messaging API 用戶端與桌面 GUI 自動化控制器。
- 對外僅提供極簡公開介面：
  - `deliver_text(to_user_id: str, text: str) -> bool`
  - `deliver_image(to_user_id: str, image_path: str) -> bool`

### 2. 重構 LineHandler 與相依服務

#### [MODIFY] [app/line_handler.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/line_handler.py)
- 轉為呼叫 `LineDeliveryAdapter` 的 Thin Facade，維持完全相容性。

#### [MODIFY] [app/main.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/main.py) & [app/scheduler.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/scheduler.py)
- 更新發送調用，簡化為統一的適配器入口。

### 3. 單元與整合測試

#### [NEW] [tests/test_line_delivery_adapter.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/tests/test_line_delivery_adapter.py)
- 撰寫獨立測試，驗證長訊息切割、文字與圖片發送降級機制。

---

## 🧪 驗證計畫 (Verification Plan)

### 自動化測試 (Automated Tests)
- 執行 `./venv/bin/python -m pytest tests/`
- 確保包含 `test_line_delivery_adapter.py` 在內的所有測試全數 100% 通過。

### 手動與功能驗證
- 發送長文字 Prompt，驗證自動拆分與推播。
- 發送早安圖片推播，驗證多管道適配器正常運作。
