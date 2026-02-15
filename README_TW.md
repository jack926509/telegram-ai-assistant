# Telegram AI 智能助理 🤖

> 一鍵部署到 Zeabur,5分鐘擁有你的 AI 助理!

[![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/)

## ✨ 功能特色

這是一個整合 OpenAI 的全功能 Telegram 機器人,具備:

- 📅 **智能行事曆** - 自然語言創建行程、自動提醒
- 💰 **記帳管家** - AI 自動分類、每日報表、預算管理
- 🔍 **網頁搜尋** - 搜尋並總結網頁內容
- 🌤 **天氣查詢** - 即時天氣與未來預報
- 📈 **股價查詢** - 台股/美股即時報價

## 🚀 快速部署到 Zeabur

### 為什麼選擇 Zeabur?

- 🇹🇼 **台灣團隊** - 繁體中文介面,在地支援
- ⚡ **極速部署** - 3 分鐘完成部署
- 💰 **免費方案** - 500 小時/月,個人使用綽綽有餘
- 📊 **完整監控** - 即時日誌與資源監控

### 部署步驟

#### 1️⃣ 取得 API Keys

**Telegram Bot Token:**
1. 在 Telegram 搜尋 `@BotFather`
2. 發送 `/newbot` 並按指示操作
3. 取得 Token (格式: `123456789:ABCdef...`)

**OpenAI API Key:**
1. 前往 [platform.openai.com](https://platform.openai.com/)
2. 註冊並充值 ($5-10 USD)
3. 建立 API Key (格式: `sk-...`)

**Weather API Key (可選):**
1. 前往 [openweathermap.org](https://openweathermap.org/api)
2. 註冊免費帳戶
3. 取得 API Key

#### 2️⃣ Fork 專案到 GitHub

點擊右上角的 "Fork" 按鈕,將專案複製到你的 GitHub 帳號

#### 3️⃣ 在 Zeabur 部署

1. 前往 [zeabur.com](https://zeabur.com/)
2. 使用 GitHub 登入
3. 點擊 **"Create Project"** (建立專案)
4. 點擊 **"Add Service"** → 選擇 **"Git"**
5. 選擇你剛 Fork 的專案
6. Zeabur 會自動偵測 Dockerfile 並開始建置

#### 4️⃣ 設定環境變數

在服務頁面點擊 **"Variables"** 標籤,新增以下變數:

| 變數名稱 | 說明 | 必填 |
|---------|------|------|
| `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | ✅ 必填 |
| `OPENAI_API_KEY` | OpenAI API Key | ✅ 必填 |
| `WEATHER_API_KEY` | 天氣 API Key | 可選 |
| `DATABASE_URL` | 資料庫路徑 | 預設值即可 |
| `TIMEZONE` | 時區設定 | 預設 `Asia/Taipei` |

#### 5️⃣ 完成!

- 等待 2-3 分鐘讓 Zeabur 完成部署
- 在 Telegram 搜尋你的機器人
- 發送 `/start` 開始使用!

## 📱 使用範例

### 行事曆管理
```
你: 明天下午3點開會討論Q1報告
Bot: ✅ 行程已建立!
     📅 開會討論Q1報告
     🕐 2024-02-16 15:00
     ⏰ 將在 30 分鐘前提醒您
```

### 智能記帳
```
你: 午餐 150 元
Bot: ✅ 💸 支出已記錄!
     金額: $150
     分類: 食物
     說明: 午餐
     
     📊 今日統計:
     支出: $150
     收入: $0
```

### 天氣查詢
```
你: /weather 台北
Bot: 🌍 台北 天氣
     🌤 多雲
     🌡 溫度: 18°C (體感 16°C)
     💧 濕度: 75%
```

### 股價查詢
```
你: /stock 2330
Bot: 📊 台灣積體電路 (2330.TW)
     💰 現價: 685.00 TWD
     📈 漲跌: +5.00 (+0.73%)
```

## 🎯 完整功能

### 行事曆功能
- ✅ 自然語言創建: "明天下午3點開會"
- ✅ 查詢行程: "本週的行程"
- ✅ 刪除行程: "刪除明天的會議"
- ✅ 自動提醒 (事前 30 分鐘)

### 記帳功能
- ✅ 記錄支出: "午餐 150 元"
- ✅ 記錄收入: "收入 30000 薪水"
- ✅ 查詢統計: "今天花了多少"、"本月支出"
- ✅ 預算管理: `/setbudget 30000`
- ✅ 每日報表 (晚上 8 點自動發送)
- ✅ 月度報表 (每月 1 號自動發送)

### 網頁搜尋
- ✅ 關鍵字搜尋: `/search Python 教學`
- ✅ 網頁總結: `/summarize https://example.com`
- ✅ 智能觸發: 直接說 "搜尋..." 或 "查詢..."

### 天氣查詢
- ✅ 即時天氣: `/weather 台北`
- ✅ 未來預報: `/forecast 台北`
- ✅ 支援全球城市

### 股票功能
- ✅ 股價查詢: `/stock 2330` (台股) 或 `/stock AAPL` (美股)
- ✅ 走勢圖: `/chart 2330`
- ✅ 熱門股票: `/watchlist`

## 🛠 進階設定

### 持久化資料

如果需要在重啟後保留資料:

1. 在 Zeabur 服務頁面點擊 **"Volumes"**
2. 點擊 **"Add Volume"**
3. 設定掛載路徑: `/app/data`
4. 資料庫會被持久化保存

### 自動部署

每次推送到 GitHub,Zeabur 會自動重新部署:

```bash
git add .
git commit -m "Update features"
git push origin main
```

### 監控與日誌

- **即時日誌**: 點擊 "Logs" 標籤查看運行狀況
- **資源監控**: 點擊 "Metrics" 標籤查看 CPU/記憶體使用
- **重啟服務**: 點擊右上角 "Restart" 按鈕

## 💰 費用說明

### 免費方案

- ⚡ 500 小時/月執行時間
- 💾 1GB 儲存空間
- 🌐 100GB 流量
- 🔧 無限專案數

**個人使用完全免費!** 機器人 24/7 運行約需 720 小時/月,建議使用付費方案。

### 開發者方案 ($5/月)

- ⚡ 無限執行時間
- 💾 5GB 儲存空間
- 🌐 500GB 流量
- 🎯 更高優先級

## 📚 相關文件

- [詳細部署指南](ZEABUR_DEPLOYMENT.md) - 完整圖文教學
- [快速開始](QUICKSTART.md) - 5 分鐘上手指南
- [專案說明](README.md) - 完整專案文件

## ❓ 常見問題

**Q: 機器人沒有回應?**
A: 檢查環境變數是否正確設定,查看 Zeabur 的 Logs 標籤找出錯誤。

**Q: OpenAI API 錯誤?**
A: 確認 API Key 正確且帳戶有餘額。

**Q: 如何更新機器人?**
A: 修改程式碼後 `git push`,Zeabur 會自動重新部署。

**Q: 資料會遺失嗎?**
A: 建議設定 Persistent Volume 保存資料庫。

## 🆘 需要幫助?

- 📖 查看 [完整文件](ZEABUR_DEPLOYMENT.md)
- 🐛 回報問題請開 [GitHub Issue](../../issues)
- 💬 加入 [Zeabur Discord](https://discord.gg/zeabur)

## 📝 授權

MIT License - 可自由使用與修改

---

**現在就部署你的 AI 助理!** 👉 [![Deploy on Zeabur](https://zeabur.com/button.svg)](https://zeabur.com/)

製作於台灣 🇹🇼 with ❤️
