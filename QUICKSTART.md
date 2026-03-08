# 快速開始指南

## 🚀 5分鐘啟動你的 AI 助理

### 步驟一: 取得 API Keys

#### 1. Telegram Bot Token
1. 打開 Telegram,搜尋 `@BotFather`
2. 發送 `/newbot`
3. 輸入機器人名稱 (例如: `My AI Assistant`)
4. 輸入機器人用戶名 (必須以 `bot` 結尾,例如: `my_ai_assistant_bot`)
5. 複製收到的 **Token** (格式: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

#### 2. OpenAI API Key
1. 前往 https://platform.openai.com/
2. 註冊/登入帳戶
3. 點擊右上角頭像 → "View API keys"
4. 點擊 "Create new secret key"
5. 複製 API Key (格式: `sk-...`)
6. **重要**: 需要充值帳戶才能使用 API (建議先充值 $5-10 USD)

#### 3. Weather API Key (可選,但建議取得)
1. 前往 https://openweathermap.org/api
2. 點擊 "Sign Up" 註冊免費帳戶
3. 驗證電子郵件
4. 在 Dashboard 找到你的 API Key
5. 免費方案足夠使用!

---

### 步驟二: 設定環境變數

1. 複製 `.env.example` 為 `.env`:
   ```bash
   cp .env.example .env
   ```

2. 編輯 `.env` 檔案,填入你的 API Keys:
   ```env
   TELEGRAM_BOT_TOKEN=你的_telegram_token
   OPENAI_API_KEY=你的_openai_key
   WEATHER_API_KEY=你的_weather_key
   ```

---

### 步驟三: 部署 (選擇一種方式)

#### 方法 A: Zeabur 部署 (推薦 🇹🇼)

**最簡單的雲端部署方式!**

1. 上傳到 GitHub (如果還沒有):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/你的帳號/telegram-ai-assistant.git
   git push -u origin main
   ```

2. 前往 [Zeabur](https://zeabur.com/)
3. 使用 GitHub 登入
4. 點擊 "Create Project"
5. 選擇 "Add Service" → "Git"
6. 選擇你的專案
7. 在 "Variables" 設定環境變數
8. 自動部署完成!

**詳細教學:** 請看 [ZEABUR_DEPLOYMENT.md](ZEABUR_DEPLOYMENT.md)

#### 方法 B: 本地運行 (開發測試用)
**使用啟動腳本 (推薦):**
```bash
./start.sh
```

#### 方法 C: 手動安裝
```bash
# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt

# 啟動機器人
python bot.py
```

#### 方法 D: 使用 Docker
```bash
# 建立並啟動容器
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

---

### 步驟四: 測試機器人

1. 打開 Telegram
2. 搜尋你的機器人名稱 (例如: `@my_ai_assistant_bot`)
3. 點擊 "Start" 或發送 `/start`
4. 應該會收到歡迎訊息!

---

## ✨ 開始使用

### 行事曆管理
```
你: 明天下午3點開會
bot: ✅ 行程已建立!
     📅 開會
     🕐 2024-02-16 15:00
     ⏰ 將在 30 分鐘前提醒您

你: 本週的行程
bot: 📅 未來一週的行程:
     • 開會
       🕐 02/16 15:00
```

### 記帳功能
```
你: 午餐 150 元
bot: ✅ 💸 支出已記錄!
     金額: $150
     分類: 食物
     
     📊 今日統計:
     支出: $150
     收入: $0
     淨額: -$150

你: 今天花了多少
bot: 💰 財務總結
     📅 日期: 2024-02-15
     💸 支出: $150
     💵 收入: $0
     📊 淨額: -$150
```

### 天氣查詢
```
你: /weather 台北
bot: 🌍 台北 天氣
     🌤 多雲
     🌡 溫度: 18°C (體感 16°C)
     💧 濕度: 75%
     💨 風速: 3.2 m/s
```

### 網頁搜尋
```
你: /search Python 教學
bot: 🔍 搜尋結果: Python 教學
     1. Python 官方教學
        https://docs.python.org/zh-tw/3/tutorial/
        ...
```

---

## 🎯 進階功能

### 設定月度預算
```
/setbudget 30000
```

### 查詢未來天氣
```
/forecast 台北
```

---

## ❓ 常見問題

### Q: 機器人沒有回應?
A: 檢查:
1. 環境變數是否正確設定
2. 查看終端機是否有錯誤訊息
3. 確認網路連線正常
4. Telegram Bot Token 是否有效

### Q: OpenAI API 錯誤?
A: 
1. 確認 API Key 正確
2. 檢查帳戶是否有餘額
3. 查看 https://platform.openai.com/usage

### Q: 如何停止機器人?
A: 在終端機按 `Ctrl + C`

### Q: 如何更新機器人?
A:
```bash
git pull
pip install -r requirements.txt
python bot.py
```

---

## 📱 手機使用建議

1. **設定快捷指令**: 在 Telegram 聊天中輸入 `/` 可以看到所有指令
2. **釘選機器人**: 在聊天列表長按機器人,選擇"釘選"
3. **通知設定**: 建議開啟行程提醒通知

---

## 🎓 學習資源

- [Telegram Bot API 文件](https://core.telegram.org/bots/api)
- [OpenAI API 文件](https://platform.openai.com/docs)
- [Python Telegram Bot 教學](https://github.com/python-telegram-bot/python-telegram-bot/wiki)

---

## 💡 使用技巧

1. **自然語言**: 直接用自然語言跟機器人對話,它會智能判斷你的需求
2. **快速記帳**: 直接說"午餐 150"即可,不需要輸入完整指令
3. **行程提醒**: 系統會在事件前 30 分鐘自動提醒
4. **每日報表**: 每晚 8 點會收到當日花費總結
5. **月度報表**: 每月 1 號會收到上月財務報表

---

## 🆘 需要幫助?

- 📧 開啟 GitHub Issue
- 💬 查看 README.md
- 📖 閱讀 DEPLOYMENT.md

祝你使用愉快! 🎉
