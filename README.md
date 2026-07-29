# Antigravity Line Bot Bridge (雙向溝通控制管道)

透過 Line Messaging API 與 FastAPI Webhook，直接控制 Google Antigravity Agent 的雙向溝通工具。

---

## 🌟 核心特色

1. **雙向互動與控制**：在 Line 上發送 Prompt 即可觸發 Antigravity Agent 推論與執行任務。
2. **Google Search Grounding (即時連網搜尋)**：原生整合 Gemini 2.5/2.0 即時 Google 搜尋能力，查詢最新頭條新聞與即時資訊。
3. **非同步推播模式 (Async Push Message)**：接收 Webhook 後秒回 200 OK，任務完成後主動推播結果。
4. **白名單安全性驗證**：只有指定 `ALLOWED_USER_IDS` 的 Line 帳號才可以下達控制指令。
5. **Session 記憶維護**：自動延續使用者的對話 context，並提供 `/reset` 等控制指令。

---

## 🔍 如何查詢您的 Line User ID？

在 Line 中取得此 `User ID`（以 `U` 開頭的 33 字元字串）有以下兩種最快捷的方法：

### 方法一：從 Line Developers Console 直接查看（最推薦）
1. 開啟並登入 [Line Developers Console](https://developers.line.biz/)。
2. 點選您的 Provider 與建立了 Messaging API 的 Channel。
3. 在 **Basic settings** 分頁中，拉到頁面最下方。
4. 即可看到 **Your user ID**（例如 `U1234567890abcdef1234567890abcdef`），將其複製貼至 `.env` 的 `ALLOWED_USER_IDS` 即可！

### 方法二：透過本服務的 Webhook Log 查詢
1. 先將 `.env` 中的 `ALLOWED_USER_IDS` 留空或設為任意值，並啟動 FastAPI Webhook 服務。
2. 在 Line 上向您的 Line Bot 隨意發送一則訊息（如 `hello`）。
3. 觀察終端機中 FastAPI 服務印出的 Log，即可看到被拒絕或收到的 User ID 資訊：
   ```
   [WARNING] main: 拒絕未授權的使用者存取: U1234567890abcdef1234567890abcdef
   ```
4. 複製該 Log 中的 `U...` 字串貼入 `.env` 並重新啟動服務即可完成授權。

---

## 🛠️ 控制指令列表

在 Line 聊天視窗中輸入：
- `任何 Prompt 敘述`：直接觸發 Antigravity Agent 執行任務與即時網路搜尋。
- `/status`：查詢當前系統與 Agent 任務狀態。
- `/reset` 或 `/clear`：重置並清除目前的對話歷史紀錄。
- `/help`：顯示系統說明選單。

---

## 🚀 快速開始

### 1. 設定環境變數

複製設定檔範本並填入金鑰：

```bash
cp .env.example .env
```

請編輯 `.env` 並填入：
- `LINE_CHANNEL_SECRET` (Line Developers Console -> Basic settings)
- `LINE_CHANNEL_ACCESS_TOKEN` (Line Developers Console -> Messaging API)
- `ALLOWED_USER_IDS` (您的 Line User ID，多個請用逗號分隔)
- `GEMINI_API_KEY` (Google AI Studio API Key)

### 2. 本地開發與啟動

建議使用 Python 內建的 `venv` 建立獨立虛擬環境：

```bash
# 建立 Python 虛擬環境 (名稱為 venv)
python3 -m venv venv

# 啟動虛擬環境 (macOS / Linux)
source venv/bin/activate

# 在虛擬環境中安裝依賴套件
pip install -r requirements.txt

# 啟動 FastAPI 服務
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --reload-dir app
```

---

## 🔗 ngrok 本地測試教學

Line Messaging API 的 Webhook 需要對外的公網 HTTPS 網址。在本地測試時可使用 `ngrok`：

1. 安裝並啟動 ngrok：
   ```bash
   ngrok http 8000
   ```
2. 複製 ngrok 產生的 HTTPS Forwarding 網址（如 `https://xxxx.ngrok-free.app`）。
3. 前往 [Line Developers Console](https://developers.line.biz/)：
   - 進入您的 Channel -> **Messaging API** 頁面
   - 設定 **Webhook URL** 為：`https://xxxx.ngrok-free.app/webhook`
   - 勾選 **Use webhook**
   - 點擊 **Verify** 測試連線狀態

---

## 🐳 Docker 部署說明

如果不想在本地設定 Python 環境，亦可使用 Docker Compose 一鍵構建與啟動：

```bash
docker-compose up -d --build
```

檢視服務日誌：
```bash
docker-compose logs -f
```

停止服務：
```bash
docker-compose down
```
