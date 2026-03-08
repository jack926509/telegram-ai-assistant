# Telegram AI 智能助理 - 專案總覽

## 📁 專案結構

```
telegram-ai-assistant/
├── bot.py                      # 主程式入口
├── config.py                   # 設定檔
├── requirements.txt            # Python 依賴
├── .env.example               # 環境變數範例
├── .gitignore                 # Git 忽略檔案
├── Dockerfile                 # Docker 映像設定
├── docker-compose.yml         # Docker Compose 設定
├── start.sh                   # 快速啟動腳本
├── upload-to-github.sh        # GitHub 上傳腳本
│
├── README.md                  # 專案說明
├── QUICKSTART.md             # 快速開始指南
├── DEPLOYMENT.md             # 部署指南
├── LICENSE                    # 授權文件
│
├── database/                  # 資料庫模組
│   ├── __init__.py
│   ├── models.py             # 資料模型 (SQLAlchemy)
│   └── operations.py         # 資料庫操作
│
├── handlers/                  # 功能處理器
│   ├── __init__.py
│   ├── calendar.py           # 行事曆功能
│   ├── expense.py            # 記帳功能
│   ├── search.py             # 網頁搜尋
│   └── weather.py            # 天氣查詢
│
├── utils/                     # 工具函數
│   ├── __init__.py
│   ├── openai_helper.py      # OpenAI API 整合
│   └── scheduler.py          # 排程系統
│
├── data/                      # 資料目錄 (自動建立)
│   └── assistant.db          # SQLite 資料庫
│
└── .github/                   # GitHub Actions
    └── workflows/
        └── test.yml          # 自動測試
```

---

## 🎯 核心功能

### 1. 行事曆管理 (`handlers/calendar.py`)
- ✅ 創建行程 (自然語言解析)
- ✅ 查詢行程 (今天/本週/本月)
- ✅ 刪除行程
- ✅ 自動提醒 (可設定提前時間)
- 🔄 修改行程 (開發中)

**技術特點:**
- 使用 OpenAI 解析自然語言
- SQLAlchemy ORM 管理資料
- APScheduler 處理定時提醒

### 2. 記帳功能 (`handlers/expense.py`)
- ✅ 記錄支出/收入
- ✅ 自動分類 (食物/交通/娛樂等)
- ✅ 每日花費總結
- ✅ 月度財務報表
- ✅ 預算設定與警告
- ✅ 分類統計

**技術特點:**
- AI 智能分類支出
- 自動化每日/月度報表
- 支援多幣別 (預設 TWD)

### 3. 網頁搜尋 (`handlers/search.py`)
- ✅ DuckDuckGo 搜尋 (無需 API key)
- ✅ 網頁內容抓取
- ✅ AI 總結網頁內容
- ✅ 智能搜尋 (關鍵字觸發)

**技術特點:**
- BeautifulSoup 解析 HTML
- OpenAI 總結內容
- 自動過濾無用內容

### 4. 天氣查詢 (`handlers/weather.py`)
- ✅ 即時天氣資訊
- ✅ 未來天氣預報
- ✅ 支援多種 API (OpenWeatherMap / wttr.in)
- ✅ 天氣圖示與描述

**技術特點:**
- 雙 API 支援 (有/無 key 都能用)
- 繁體中文天氣描述
- 詳細氣象資訊

---

## 🔧 技術架構

### 核心技術棧
- **語言**: Python 3.11
- **Bot 框架**: python-telegram-bot 20.7
- **AI 引擎**: OpenAI GPT-4o-mini
- **資料庫**: SQLite + SQLAlchemy
- **排程**: APScheduler
- **網頁解析**: BeautifulSoup4

### 資料庫設計

#### CalendarEvent (行事曆事件)
```python
- id: 主鍵
- user_id: 使用者 ID
- title: 事件標題
- description: 事件描述
- start_time: 開始時間
- end_time: 結束時間
- reminder_time: 提醒時間
- is_reminded: 是否已提醒
- created_at: 建立時間
- updated_at: 更新時間
```

#### Expense (支出/收入)
```python
- id: 主鍵
- user_id: 使用者 ID
- amount: 金額
- category: 分類
- description: 描述
- transaction_type: 類型 (expense/income)
- date: 日期
- created_at: 建立時間
```

#### UserPreference (使用者偏好)
```python
- id: 主鍵
- user_id: 使用者 ID
- default_currency: 預設幣別
- reminder_enabled: 是否啟用提醒
- daily_reminder_time: 每日提醒時間
- monthly_budget: 月度預算
- created_at: 建立時間
- updated_at: 更新時間
```

### AI 整合流程

```
使用者訊息
    ↓
判斷意圖類型
    ↓
├─ 行事曆 → OpenAI 解析 → 資料庫操作
├─ 記帳   → OpenAI 解析 → 資料庫操作
├─ 搜尋   → DuckDuckGo → OpenAI 總結
├─ 天氣   → Weather API → 格式化輸出
└─ 一般   → OpenAI 對話 → 直接回應
```

---

## 📊 系統需求

### 最低需求
- Python 3.9+
- 512 MB RAM
- 500 MB 磁碟空間
- 網路連線

### 推薦配置
- Python 3.11+
- 1 GB RAM
- 1 GB 磁碟空間
- 穩定網路連線

---

## 🔐 環境變數說明

| 變數名稱 | 必要性 | 說明 | 範例 |
|---------|-------|------|------|
| TELEGRAM_BOT_TOKEN | **必要** | Telegram Bot Token | `123456789:ABC...` |
| OPENAI_API_KEY | **必要** | OpenAI API Key | `sk-...` |
| WEATHER_API_KEY | 可選 | OpenWeatherMap API Key | `abc123...` |
| DATABASE_URL | 可選 | 資料庫路徑 | `sqlite:///data/assistant.db` |
| TIMEZONE | 可選 | 時區設定 | `Asia/Taipei` |
| OPENAI_MODEL | 可選 | OpenAI 模型 | `gpt-4o-mini` |

---

## 🚀 部署選項

### 1. Zeabur (強烈推薦 🇹🇼)
- ✅ 台灣團隊,繁中介面
- ✅ 最簡單
- ✅ 速度最快
- ✅ 免費額度充足
- ❌ 較新平台

### 2. Railway
- ✅ 簡單
- ✅ 自動部署
- ✅ 免費額度
- ❌ 額度有限

### 2. Render
- ✅ 完全免費
- ✅ 容易設定
- ❌ 會休眠

### 3. Fly.io
- ✅ 不休眠
- ✅ 免費額度大
- ❌ 設定稍複雜

### 4. VPS
- ✅ 完全控制
- ✅ 無限制
- ❌ 需要管理

詳細部署步驟請參考 `DEPLOYMENT.md`

---

## 📈 效能指標

### API 呼叫
- OpenAI: 每次對話約 500-2000 tokens
- 天氣: 每次查詢 1 API call

### 資料庫
- SQLite 輕量級
- 單檔案易於備份
- 適合個人使用

### 記憶體使用
- 基本運行: ~50 MB
- 高峰使用: ~150 MB

---

## 🔒 安全性

### 已實作
- ✅ 環境變數儲存敏感資訊
- ✅ .gitignore 防止洩漏
- ✅ 使用者資料隔離
- ✅ SQL injection 防護 (ORM)

### 建議加強
- 🔄 加密資料庫
- 🔄 使用者認證
- 🔄 Rate limiting
- 🔄 日誌加密

---

## 🧪 測試

### 手動測試
```bash
# 啟動機器人
python bot.py

# 在 Telegram 測試各項功能
/start
/help
創建行程: 明天下午3點開會
記帳: 午餐 150 元
/weather 台北
```

### 自動測試 (開發中)
- 單元測試
- 整合測試
- E2E 測試

---

## 📝 開發路線圖

### v1.0 (當前)
- ✅ 基本功能完成
- ✅ 所有核心模組
- ✅ 部署文件

### v1.1 (計劃中)
- 🔄 行程修改功能
- 🔄 多語言支援
- 🔄 語音訊息處理
- 🔄 圖片辨識

### v2.0 (未來)
- 🔄 群組功能
- 🔄 協作記帳
- 🔄 進階報表
- 🔄 自訂提醒規則

---

## 🤝 貢獻指南

歡迎貢獻!請遵循以下步驟:

1. Fork 專案
2. 建立功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交變更 (`git commit -m 'Add amazing feature'`)
4. 推送分支 (`git push origin feature/amazing-feature`)
5. 開啟 Pull Request

---

## 📞 支援

- 📧 開啟 GitHub Issue
- 💬 討論區
- 📖 閱讀文件

---

## 📄 授權

MIT License - 詳見 `LICENSE` 檔案

---

## 🙏 致謝

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [OpenAI](https://openai.com/)
- [yfinance](https://github.com/ranaroussi/yfinance)
- 所有貢獻者

---

最後更新: 2024-02-15
