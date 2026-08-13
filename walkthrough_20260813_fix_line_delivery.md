# Line Bot 訊息傳送連線修復 Walkthrough (2026-08-13)

已成功完成 **Line Bot 訊息傳送連線修復**，解決 FastAPI 與 ngrok 外網連線中斷與 IPv6 地址綁定連線拒絕的問題。

---

## 📦 變更細節與修復內容

1. **一鍵啟動腳本強化 ([start.sh](file:///Users/johnkuo/Library/CloudStorage/GoogleDrive-johnyhkuo@gmail.com/我的雲端硬碟/worktemp/Antigravity-Line/start.sh))**
   - 加入 `disown` 守護機制，防止因 Shell 退場導致子進程收到 SIGHUP 而被打掉。
   - 將 ngrok 綁定由泛用 `8000` 精確限定為 IPv4 `127.0.0.1:8000`，解決 macOS 下 localhost 優先解析為 IPv6 `::1` 造成的 `ERR_NGROK_8012` Connection Refused。
2. **服務狀態與端點驗證**
   - 本地健康端點 `http://127.0.0.1:8000/health`: **`{"status":"ok"}` 🟢**
   - 外網 ngrok 公開隧道: **`https://professed-equivocal-lagoon.ngrok-free.dev/webhook` 🟢**
   - 模擬 LINE POST 請求回應: **`{"status":"no events"}` (HTTP 200 OK) 🟢**

---

## 🧪 驗收結果 (Acceptance Criteria Status)

1. **服務正常連線**：`http://127.0.0.1:8000/health` 回傳 `status: ok` ✅
2. **ngrok 隧道在線**：`http://127.0.0.1:4040/api/tunnels` 成功取得公開 HTTPS URL ✅
3. **Webhook 異步秒回**：外網 `POST /webhook` 成功回傳 HTTP 200 OK ✅
4. **早安訊息排程程式完全未受影響**：100% 符合 Guardrail Spec 禁區紅線 ✅
