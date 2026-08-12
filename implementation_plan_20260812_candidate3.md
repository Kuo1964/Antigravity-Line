# Candidate 3: MacSystemGateway 模組深化導入計畫 (2026-08-12)

本計畫旨在針對 **Candidate 3: MacSystemGateway** 進行代碼深化重構，解決解鎖螢幕 (`mac_unlocker.py`)、螢幕狀態記憶 (`macos_ui_adapter.py`) 與早安圖片爬取 (`image_crawler.py`) 邏輯分散、缺乏單一領域閘道器的問題。

---

## 🎯 核心目標與原則

1. **高槓桿與深介面 (Deep Module)**：
   將 PyAutoGUI 模擬、cclog 鎖屏狀態檢測、螢幕狀態復原與網路圖片爬取重試邏輯徹底隱藏於閘道器後。
2. **極簡語義化介面 (Interface Simplicity)**：
   呼叫端（如 `scheduler.py` 與 `scheduler_service.py`）僅需傳送 `ensure_unlocked_and_ready()` 或 `fetch_morning_media()`。
3. **完整保留歷史規劃**：
   依專案規範，本檔儲存為 `implementation_plan_20260812_candidate3.md` 以永久保留歷程。

---

## 📂 預計變更檔案 (Proposed Changes)

### 1. 新增 MacSystemGateway 核心深層系統閘道器

#### [NEW] [app/services/mac_system_gateway.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/services/mac_system_gateway.py)
- 定義 `MacSystemGateway` 類別。
- 內部整合解鎖解密控制器、螢幕適配器與多來源圖片爬蟲。
- 對外僅提供極簡公開介面：
  - `ensure_unlocked_and_ready() -> bool`
  - `restore_display_state() -> bool`
  - `fetch_morning_media(keyword: str = "good morning") -> Optional[str]`

### 2. 重構專案次級服務與排程器

#### [MODIFY] [app/services/mac_unlocker.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/services/mac_unlocker.py) & [app/services/image_crawler.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/services/image_crawler.py)
- 轉為 Thin Facade，維持向下相容性。

#### [MODIFY] [app/scheduler.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/scheduler.py) & [app/services/scheduler_service.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/app/services/scheduler_service.py)
- 更新發送與喚醒調用，採用統一的閘道器入口。

### 3. 單元與整合測試

#### [NEW] [tests/test_mac_system_gateway.py](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/tests/test_mac_system_gateway.py)
- 撰寫獨立測試，驗證喚醒狀態檢查、螢幕狀態恢復與圖片抓取流程。

---

## 🧪 驗證計畫 (Verification Plan)

### 自動化測試 (Automated Tests)
- 執行 `./venv/bin/python -m pytest tests/`
- 確保包含 `test_mac_system_gateway.py` 在內的所有測試全數 100% 通過。

### 手動與功能驗證
- 驗證 `ensure_unlocked_and_ready()` 方法防護邏輯。
- 驗證早安圖片抓取與快取正常。
