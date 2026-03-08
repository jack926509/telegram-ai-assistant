# Telegram AI 智能助理

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/)

這是一個功能完整的 Telegram AI 助理機器人,整合了 OpenAI API,提供以下功能:

## 功能特色

1. **行事曆管理** 📅
   - 創建行程
   - 修改行程
   - 查詢行程
   - 自動提醒

2. **記帳功能** 💰
   - 記錄支出/收入
   - 每日花費提醒
   - 月度統計報表
   - 消費分類

3. **網頁查詢** 🔍
   - 搜尋網頁資訊
   - 總結網頁內容

4. **天氣查詢** ⛅
   - 即時天氣資訊
   - 多日天氣預報

## 技術架構

- **Bot Framework**: python-telegram-bot
- **AI 引擎**: OpenAI API (GPT-4)
- **資料庫**: SQLite
- **排程系統**: APScheduler
- **部署**: Docker / Railway / Render

## 快速開始

### 1. 環境需求

- Python 3.9+
- Telegram Bot Token
- OpenAI API Key

### 2. 安裝步驟

```bash
# 克隆專案
git clone https://github.com/yourusername/telegram-ai-assistant.git
cd telegram-ai-assistant

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數
cp .env.example .env
# 編輯 .env 填入你的 API keys
```

### 3. 設定環境變數

在 `.env` 檔案中設定:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
WEATHER_API_KEY=your_openweathermap_api_key
DATABASE_URL=sqlite:///assistant.db
DB_AUTO_MIGRATE=true
DB_ECHO=false
```

> 正式環境（Zeabur）建議使用 PostgreSQL：
> `postgresql+psycopg2://<user>:<password>@<host>:5432/<db>`

### 4. 取得 API Keys

#### Telegram Bot Token
1. 在 Telegram 搜尋 [@BotFather](https://t.me/botfather)
2. 發送 `/newbot` 並依指示建立機器人
3. 取得 Bot Token

#### OpenAI API Key
1. 前往 [OpenAI Platform](https://platform.openai.com/)
2. 註冊並充值帳戶
3. 建立 API Key

#### Weather API Key (免費)
1. 前往 [OpenWeatherMap](https://openweathermap.org/api)
2. 註冊免費帳戶
3. 取得 API Key

### 5. 執行機器人

```bash
python bot.py
```

## 使用說明

### 指令列表

- `/start` - 啟動機器人
- `/help` - 顯示幫助訊息
- `/calendar` - 行事曆管理
- `/expense` - 記帳功能
- `/search` - 網頁搜尋
- `/weather` - 天氣查詢

### 使用範例

**行事曆:**
```
創建行程: 明天下午3點開會
查詢行程: 本週的行程
刪除行程: 刪除明天的會議
```

**記帳:**
```
記帳: 午餐 150 元
記帳: 收入 30000 薪水
查詢: 本月花費
查詢: 今天花了多少
```

**天氣:**
```
天氣: 台北
天氣: 台北 未來三天
```

## Docker 部署

```bash
# 建立 Docker 映像
docker build -t telegram-ai-assistant .

# 執行容器
docker run -d \
  --name telegram-bot \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  telegram-ai-assistant
```

## 部署選項

### Zeabur (強烈推薦 🇹🇼)
Zeabur 是台灣團隊開發的部署平台,介面友善且支援繁體中文!

1. Fork 此專案到你的 GitHub
2. 前往 [Zeabur](https://zeabur.com/)
3. 使用 GitHub 登入
4. 點擊 "Create Project"
5. 選擇 "Deploy from GitHub"
6. 選擇你的專案
7. 在 Variables 設定環境變數:
   - `TELEGRAM_BOT_TOKEN`
   - `OPENAI_API_KEY`
   - `WEATHER_API_KEY`
8. 自動偵測 Dockerfile 並部署
9. 部署完成!

**Zeabur 優勢:**
- 🇹🇼 台灣團隊,繁體中文介面
- ⚡ 部署速度快
- 💰 免費額度充足
- 🎯 自動 HTTPS
- 📊 完整監控面板

### Railway
1. Fork 此專案到你的 GitHub
2. 前往 [Railway](https://railway.app/)
3. 點擊 "New Project" → "Deploy from GitHub repo"
4. 選擇你的專案並設定環境變數
5. 部署完成!

### Render
1. 前往 [Render](https://render.com/)
2. 點擊 "New Web Service"
3. 連接 GitHub 專案
4. 設定環境變數
5. 點擊 "Create Web Service"

### VPS 部署
```bash
# 使用 systemd 建立服務
sudo nano /etc/systemd/system/telegram-bot.service

# 啟動服務
sudo systemctl start telegram-bot
sudo systemctl enable telegram-bot
```

## 專案結構

```
telegram-ai-assistant/
├── bot.py                 # 主程式入口
├── config.py             # 設定檔
├── handlers/             # 指令處理器
│   ├── calendar.py       # 行事曆功能
│   ├── expense.py        # 記帳功能
│   ├── search.py         # 搜尋功能
│   └── weather.py        # 天氣功能
├── database/             # 資料庫模組
│   ├── models.py         # 資料模型
│   └── operations.py     # 資料庫操作
├── utils/                # 工具函數
│   ├── openai_helper.py  # OpenAI 整合
│   └── scheduler.py      # 排程系統
├── requirements.txt      # Python 依賴
├── Dockerfile           # Docker 設定
├── .env.example         # 環境變數範例
└── README.md            # 專案說明
```

## 注意事項

1. **API 用量**: OpenAI API 會產生費用,請監控使用量
2. **資料備份**: 定期備份 SQLite 資料庫
3. **安全性**: 不要將 `.env` 檔案上傳到 GitHub
4. **費率限制**: 注意各 API 的呼叫限制

## 進階功能 (未來開發)

- [ ] 多語言支援
- [ ] 語音訊息處理
- [ ] 圖片辨識
- [ ] 群組管理功能
- [ ] 個人化設定
- [ ] 資料匯出功能

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request!

## 作者

你的名字

## 支援

如有問題請開啟 Issue 或聯繫 [你的聯絡方式]
