# AI 助理程式碼審查報告

> 審查日期: 2026-02-18

---

## 一、現有功能摘要

| 模組 | 功能 | 狀態 |
|------|------|------|
| 行事曆 (calendar) | 建立/查詢/刪除行程、自動提醒 | ⚠️ 修改功能未實作 |
| 記帳 (expense) | 記錄收支、查詢報表、月度預算 | ✅ 可用 |
| 搜尋 (search) | DuckDuckGo 搜尋、網頁摘要 | ⚠️ URL 解析問題 |
| 天氣 (weather) | 即時天氣、未來預報 | ✅ 可用 |
| AI 對話 | 多輪對話、意圖路由 | ⚠️ 記憶體問題 |

---

## 二、問題清單與改善建議

### 🔴 高優先度 (影響功能正確性或安全性)

---

#### 1. 阻塞主事件迴圈 (Event Loop Blocking)

**位置:** `handlers/calendar.py:20`, `handlers/expense.py:18`

**問題:**
`parse_calendar_intent()` 和 `parse_expense_intent()` 是同步函式，在 async handler 中直接呼叫會阻塞整個 Telegram bot 的事件迴圈，導致其他使用者的訊息無法即時處理。

```python
# 現在 (會阻塞 event loop)
intent_data = ai_helper.parse_calendar_intent(message_text)

# 應改為
intent_data = await asyncio.to_thread(ai_helper.parse_calendar_intent, message_text)
```

**修改範圍:** `handlers/calendar.py`, `handlers/expense.py`

---

#### 2. 對話歷史僅存記憶體，重啟即消失

**位置:** `bot.py:42`

**問題:**
```python
conversation_history = {}  # 重啟後全部消失
```
所有使用者的對話歷史儲存在全域 dict，每次重啟後清空，使用者體驗差。同時多個同步訊息可能產生 race condition（dict 非 thread-safe）。

**建議:**
- 將對話歷史寫入資料庫（新增 `ConversationHistory` 資料表）
- 或使用 Redis 做快取層

---

#### 3. OpenAI 回應 JSON 解析脆弱

**位置:** `utils/openai_helper.py:60-62`, `98-101`

**問題:**
```python
try:
    response = OpenAIHelper.chat_completion(messages, temperature=0.3)
    return json.loads(response)
except:
    return {"intent": "unknown", "error": "無法解析意圖"}
```
OpenAI 有時回傳帶有 markdown 包裝的 JSON（例如 ` ```json {...} ``` `），`json.loads()` 無法解析，導致功能靜默失敗。

**建議:**
```python
import re
def _extract_json(text: str) -> dict:
    # 移除 markdown code block
    match = re.search(r'```(?:json)?\s*([\s\S]+?)\s*```', text)
    if match:
        text = match.group(1)
    return json.loads(text.strip())
```

---

#### 4. 錯誤訊息洩漏內部資訊

**位置:** `handlers/search.py:102`, `handlers/weather.py:27,216`

**問題:**
```python
await update.message.reply_text(f"搜尋時發生錯誤: {str(e)}")
```
直接將 exception 訊息回傳給使用者，可能洩露內部路徑、API 金鑰殘片、stack trace 等敏感資訊。

**建議:**
- 只回傳使用者友善的通用錯誤訊息
- 使用 `logger.exception()` 記錄詳細錯誤到日誌

---

#### 5. `python-dateutil` 未列入 requirements.txt

**位置:** `handlers/calendar.py:6`

**問題:**
```python
from dateutil import parser  # python-dateutil 套件
```
`requirements.txt` 中沒有 `python-dateutil`，部署到新環境時會因缺少依賴而啟動失敗。

**修正:** 在 `requirements.txt` 加入 `python-dateutil>=2.8`

---

### 🟡 中優先度 (影響使用者體驗或程式碼品質)

---

#### 6. 行事曆「修改功能」未實作

**位置:** `handlers/calendar.py:191-196`

**問題:**
```python
async def handle_update_event(update, context, user_id, intent_data):
    await update.message.reply_text("修改行程功能開發中。\n...")
```
`/start` 訊息與 `parse_calendar_intent` 都支援 `update` 意圖，但處理器僅回覆「開發中」，形成功能斷層。

**建議:** 實作基本的更新流程：先搜尋符合的行程，再修改時間/描述。

---

#### 7. 搜尋結果 URL 為 DuckDuckGo 重導向連結

**位置:** `handlers/search.py:176-178`

**問題:**
DuckDuckGo HTML 搜尋回傳的 `href` 是 `//duckduckgo.com/l/?uddg=...` 格式的重導向連結，而非真實網頁 URL。`quick_search_handler` 嘗試直接 fetch 這些 URL，會導致取得的是 DuckDuckGo 中轉頁面而非目標內容。

**建議:** 解析 `uddg` 參數取得實際 URL，或改用 DuckDuckGo Instant Answer API。

---

#### 8. 意圖路由觸發詞移除邏輯有誤

**位置:** `handlers/search.py:239-242`

**問題:**
```python
for trigger in ['搜尋', '查詢', '找', 'search']:
    query = query.replace(trigger, '').strip()
```
`str.replace()` 會取代字串中所有出現的位置，例如：
- `"找到最好的找工作方法"` → `"到最好的工作方法"` (意思改變)

**建議:** 只移除開頭的觸發詞，使用 `re.sub(r'^(搜尋|查詢|找)\s*', '', query)`

---

#### 9. `FEATURES` 功能開關從未使用

**位置:** `config.py:64-70`

**問題:**
```python
FEATURES = {
    'calendar': True,
    'expense': True,
    ...
}
```
定義了功能開關但所有 handler 都未檢查此設定，無法透過環境變數停用特定功能。

**建議:** 在 `message_handler` 和各 CommandHandler 中加入功能開關檢查。

---

#### 10. AI 路由器每次呼叫都建立新 `OpenAIHelper` 實例

**位置:** `utils/intent_router.py:63`

**問題:**
```python
async def _ai_route(text: str) -> RoutingResult | None:
    ai_helper = OpenAIHelper()  # 每次都 new 一個實例
```
`OpenAIHelper` 本身無狀態，每次呼叫都重新建立是無謂的開銷。

**建議:** 改為模組層級的單例：
```python
_ai_helper: OpenAIHelper | None = None

def _get_ai_helper() -> OpenAIHelper:
    global _ai_helper
    if _ai_helper is None:
        from utils.openai_helper import OpenAIHelper
        _ai_helper = OpenAIHelper()
    return _ai_helper
```

---

#### 11. 時區不一致，datetime 未附帶時區資訊

**位置:** `database/operations.py`, `handlers/calendar.py`, `utils/scheduler.py`

**問題:**
- 所有 `datetime.now()` 回傳的是 naive datetime（無時區）
- `scheduler.py` 的 APScheduler 已設定時區 (`Asia/Taipei`)，但 `check_event_reminders` 中比較的是 naive datetime
- 部署到 UTC 伺服器時提醒時間會偏差 8 小時

**建議:**
```python
import pytz
TZ = pytz.timezone(config.TIMEZONE)

# 統一使用 timezone-aware datetime
datetime.now(tz=TZ)
```

---

#### 12. 資料庫連線：每個操作各自開啟 Session

**位置:** `database/operations.py` 所有靜態方法

**問題:**
每個 `@staticmethod` 呼叫 `get_db()` 都建立一個新的 SQLAlchemy session。單一請求可能呼叫多個方法（例如 `create_expense` + `get_daily_summary`），造成多次連線開啟/關閉的額外開銷。

**建議:** 考慮使用 context manager 或依賴注入傳遞 session，確保同一請求共用同一 session。

---

### 🟢 低優先度 (功能改善建議)

---

#### 13. 缺少速率限制 (Rate Limiting)

目前任何使用者都可以無限制傳送訊息，每筆訊息皆會呼叫 OpenAI API，可能導致：
- API 費用暴增
- 遭惡意使用者濫用

**建議:** 加入簡單的每分鐘/每日訊息數量限制，超過時回覆提示並暫停回應。

---

---

#### 15. 缺少資料匯出功能

使用者無法匯出記帳資料（例如 CSV）或備份行程。建議加入 `/export` 指令，產生 CSV 檔案供使用者下載。

---

#### 16. `setbudget` 無輸入上限驗證

**位置:** `handlers/expense.py:147`

```python
budget = float(context.args[0])
```
沒有對金額範圍做合理性驗證，使用者可輸入負數或極大值。

---

#### 17. 訊息長度未限制就送 OpenAI

使用者可傳送超長訊息（數萬字），全部送進 OpenAI API 會：
- 增加費用
- 可能超過 token 限制

**建議:** 在 `message_handler` 中加入訊息長度上限（例如 2000 字元）的預檢查。

---

## 三、改善優先順序建議

| 優先序 | 項目 | 工作量 |
|--------|------|--------|
| 1 | 修正 event loop 阻塞問題 (#1) | 小 |
| 2 | 加入 `python-dateutil` 到 requirements.txt (#5) | 極小 |
| 3 | 修正錯誤訊息洩漏 (#4) | 小 |
| 4 | 修正 OpenAI JSON 解析 (#3) | 小 |
| 5 | 修正搜尋觸發詞移除邏輯 (#8) | 小 |
| 6 | 統一時區處理 (#11) | 中 |
| 7 | 實作行事曆修改功能 (#6) | 中 |
| 8 | 對話歷史持久化 (#2) | 大 |
| 9 | 加入速率限制 (#13) | 中 |
| 10 | 功能開關落地實作 (#9) | 小 |
