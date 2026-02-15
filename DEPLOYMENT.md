# 部署指南

本指南提供多種部署方式,選擇最適合你的方案。

## 方案一: Zeabur (強烈推薦 🇹🇼)

Zeabur 是台灣團隊開發的部署平台,提供繁體中文介面和優秀的使用體驗!

### 步驟:

1. **準備 GitHub 專案**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/你的帳號/telegram-ai-assistant.git
   git push -u origin main
   ```

2. **前往 Zeabur**
   - 訪問 [zeabur.com](https://zeabur.com/)
   - 使用 GitHub 登入

3. **建立新專案**
   - 點擊 "Create Project"
   - 輸入專案名稱
   - 選擇區域: Taiwan 或 Hong Kong
   - 點擊 "Create"

4. **部署服務**
   - 點擊 "Add Service"
   - 選擇 "Git"
   - 選擇你的 GitHub 專案
   - Zeabur 會自動偵測 Dockerfile

5. **設定環境變數**
   在 Variables 標籤中加入:
   ```
   TELEGRAM_BOT_TOKEN=你的_telegram_bot_token
   OPENAI_API_KEY=你的_openai_api_key
   WEATHER_API_KEY=你的_weather_api_key
   DATABASE_URL=sqlite:///data/assistant.db
   TIMEZONE=Asia/Taipei
   ```

6. **自動部署**
   - Zeabur 會自動建置並部署
   - 等待 2-3 分鐘
   - 看到 "Running" 狀態即完成!

### Zeabur 優勢:
- 🇹🇼 台灣團隊,繁體中文介面
- ⚡ 部署速度快,亞洲節點
- 💰 免費額度充足 (500 小時/月)
- 🎯 自動偵測,一鍵部署
- 📊 完整的監控面板
- 🔄 Git push 自動部署

**詳細圖文教學請參考:** [ZEABUR_DEPLOYMENT.md](ZEABUR_DEPLOYMENT.md)

---

## 方案二: Railway

Railway 提供免費額度,非常適合個人使用。

### 步驟:

1. **準備 GitHub 專案**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/你的帳號/telegram-ai-assistant.git
   git push -u origin main
   ```

2. **前往 Railway**
   - 訪問 [railway.app](https://railway.app/)
   - 使用 GitHub 登入

3. **建立新專案**
   - 點擊 "New Project"
   - 選擇 "Deploy from GitHub repo"
   - 選擇你的 `telegram-ai-assistant` 專案

4. **設定環境變數**
   在 Railway 的 Variables 設定中加入:
   ```
   TELEGRAM_BOT_TOKEN=你的_telegram_bot_token
   OPENAI_API_KEY=你的_openai_api_key
   WEATHER_API_KEY=你的_weather_api_key
   DATABASE_URL=sqlite:///data/assistant.db
   TIMEZONE=Asia/Taipei
   ```

5. **部署**
   - Railway 會自動偵測 Dockerfile 並開始部署
   - 等待部署完成 (約 2-3 分鐘)
   - 檢查日誌確認機器人正常運行

### Railway 免費額度:
- $5 USD / 月
- 500 小時執行時間
- 適合個人使用

---

## 方案二: Render

Render 也提供免費方案,但有一些限制。

### 步驟:

1. **前往 Render**
   - 訪問 [render.com](https://render.com/)
   - 使用 GitHub 登入

2. **建立 Web Service**
   - 點擊 "New +"
   - 選擇 "Web Service"
   - 連接你的 GitHub 專案

3. **設定專案**
   ```
   Name: telegram-ai-assistant
   Environment: Docker
   Region: Singapore (離台灣最近)
   Branch: main
   ```

4. **設定環境變數**
   在 Environment 標籤中加入所有必要的環境變數

5. **部署**
   - 點擊 "Create Web Service"
   - 等待部署完成

### Render 免費額度限制:
- 閒置 15 分鐘後會休眠
- 重新啟動需要 30-60 秒
- 每月 750 小時免費

---

## 方案三: Fly.io

適合需要全天候運行的使用者。

### 步驟:

1. **安裝 Fly CLI**
   ```bash
   # macOS
   brew install flyctl
   
   # Linux
   curl -L https://fly.io/install.sh | sh
   
   # Windows
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```

2. **登入 Fly**
   ```bash
   flyctl auth login
   ```

3. **初始化專案**
   ```bash
   cd telegram-ai-assistant
   flyctl launch
   ```
   
   按照提示操作:
   - App name: telegram-ai-assistant
   - Region: Hong Kong (hkg) 或 Tokyo (nrt)
   - PostgreSQL: No
   - Redis: No

4. **設定環境變數**
   ```bash
   flyctl secrets set TELEGRAM_BOT_TOKEN="你的token"
   flyctl secrets set OPENAI_API_KEY="你的key"
   flyctl secrets set WEATHER_API_KEY="你的key"
   ```

5. **部署**
   ```bash
   flyctl deploy
   ```

6. **查看狀態**
   ```bash
   flyctl status
   flyctl logs
   ```

### Fly.io 免費額度:
- 3 個 shared-cpu VM
- 3GB 持久化儲存
- 適合 24/7 運行

---

## 方案四: VPS (完全控制)

適合有 VPS 或想要完全控制的使用者。

### 前置需求:
- Ubuntu 20.04+ VPS
- SSH 存取權限

### 步驟:

1. **連線到 VPS**
   ```bash
   ssh user@your-vps-ip
   ```

2. **安裝依賴**
   ```bash
   # 更新系統
   sudo apt update && sudo apt upgrade -y
   
   # 安裝 Docker
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   
   # 安裝 Docker Compose
   sudo apt install docker-compose -y
   
   # 安裝 Git
   sudo apt install git -y
   ```

3. **克隆專案**
   ```bash
   git clone https://github.com/你的帳號/telegram-ai-assistant.git
   cd telegram-ai-assistant
   ```

4. **設定環境變數**
   ```bash
   cp .env.example .env
   nano .env  # 編輯並填入你的 API keys
   ```

5. **使用 Docker Compose 啟動**
   ```bash
   docker-compose up -d
   ```

6. **查看日誌**
   ```bash
   docker-compose logs -f
   ```

7. **設定開機自動啟動**
   ```bash
   # Docker 已經設定 restart: unless-stopped
   # 確保 Docker 服務開機啟動
   sudo systemctl enable docker
   ```

### 管理指令:
```bash
# 停止機器人
docker-compose stop

# 重啟機器人
docker-compose restart

# 更新機器人
git pull
docker-compose up -d --build

# 查看日誌
docker-compose logs -f

# 備份資料庫
cp data/assistant.db data/assistant.db.backup
```

---

## 方案五: systemd 服務 (不使用 Docker)

適合資源受限的環境。

### 步驟:

1. **克隆專案並安裝依賴**
   ```bash
   git clone https://github.com/你的帳號/telegram-ai-assistant.git
   cd telegram-ai-assistant
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **設定環境變數**
   ```bash
   cp .env.example .env
   nano .env
   ```

3. **建立 systemd 服務**
   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```
   
   內容:
   ```ini
   [Unit]
   Description=Telegram AI Assistant
   After=network.target
   
   [Service]
   Type=simple
   User=你的使用者名稱
   WorkingDirectory=/home/你的使用者名稱/telegram-ai-assistant
   Environment="PATH=/home/你的使用者名稱/telegram-ai-assistant/venv/bin"
   ExecStart=/home/你的使用者名稱/telegram-ai-assistant/venv/bin/python bot.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

4. **啟動服務**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl start telegram-bot
   sudo systemctl enable telegram-bot
   sudo systemctl status telegram-bot
   ```

5. **管理指令**
   ```bash
   # 查看狀態
   sudo systemctl status telegram-bot
   
   # 查看日誌
   sudo journalctl -u telegram-bot -f
   
   # 重啟
   sudo systemctl restart telegram-bot
   
   # 停止
   sudo systemctl stop telegram-bot
   ```

---

## 選擇建議

| 方案 | 適合對象 | 優點 | 缺點 |
|------|---------|------|------|
| **Zeabur** | **台灣使用者、初學者** | **繁中介面、速度快、簡單** | 較新平台 |
| Railway | 國際使用者 | 簡單、自動部署 | 免費額度有限 |
| Render | 預算有限 | 免費、容易使用 | 會休眠 |
| Fly.io | 需要穩定運行 | 不休眠、免費額度大 | 設定稍複雜 |
| VPS | 進階使用者 | 完全控制、無限制 | 需要管理伺服器 |
| systemd | 資源有限 | 輕量、直接 | 需要手動管理 |

**推薦順序:**
1. 🥇 Zeabur (台灣使用者首選)
2. 🥈 Railway (國際使用者)
3. 🥉 Fly.io (需要穩定運行)

---

## 監控與維護

### 查看機器人狀態
1. 在 Telegram 發送 `/start` 給你的機器人
2. 應該會收到歡迎訊息

### 監控 API 用量
- OpenAI: https://platform.openai.com/usage
- Weather: https://home.openweathermap.org/api_keys

### 資料備份
```bash
# 如果使用 VPS
cp data/assistant.db backups/assistant-$(date +%Y%m%d).db

# 設定每日自動備份
crontab -e
# 加入: 0 2 * * * cp /path/to/data/assistant.db /path/to/backups/assistant-$(date +\%Y\%m\%d).db
```

---

## 疑難排解

### 機器人沒有回應
1. 檢查環境變數是否正確設定
2. 查看日誌檔案
3. 確認 API keys 有效
4. 測試網路連線

### OpenAI API 錯誤
- 確認 API key 正確
- 檢查帳戶餘額
- 查看 API 用量限制

### 資料庫錯誤
- 檢查 data 目錄權限
- 確認 SQLite 正常運作
- 必要時刪除 .db 檔案重建

---

## 更新機器人

### Git 更新
```bash
git pull
# Docker 環境
docker-compose up -d --build

# systemd 環境
sudo systemctl restart telegram-bot
```

### 手動更新
1. 下載新版本檔案
2. 覆蓋舊檔案
3. 重啟服務

---

## 安全建議

1. ✅ 絕不將 .env 檔案提交到 Git
2. ✅ 定期更新依賴套件
3. ✅ 定期備份資料庫
4. ✅ 監控 API 用量避免超支
5. ✅ 使用強密碼保護 VPS

---

## 需要幫助?

- 開啟 GitHub Issue
- 查看專案文件
- 加入社群討論

祝你部署順利! 🚀
