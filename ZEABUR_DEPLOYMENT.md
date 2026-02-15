# Zeabur 部署指南 🚀

Zeabur 是台灣團隊開發的現代化部署平台,提供簡單直覺的部署體驗!

## 為什麼選擇 Zeabur?

- 🇹🇼 **台灣團隊** - 繁體中文介面,在地支援
- ⚡ **速度快** - 亞洲節點,部署迅速
- 💰 **免費方案** - 提供充足的免費額度
- 🎯 **簡單易用** - 自動偵測,一鍵部署
- 📊 **完整監控** - 即時日誌與資源監控
- 🔄 **自動部署** - Git push 後自動更新

## 快速部署步驟

### 步驟 1: 準備 GitHub 專案

1. **上傳專案到 GitHub**
   ```bash
   # 如果還沒有 Git 倉庫
   git init
   git add .
   git commit -m "Initial commit"
   
   # 推送到 GitHub
   git remote add origin https://github.com/你的帳號/telegram-ai-assistant.git
   git branch -M main
   git push -u origin main
   ```

2. **確認專案包含必要檔案**
   - ✅ Dockerfile
   - ✅ requirements.txt
   - ✅ bot.py

### 步驟 2: 在 Zeabur 部署

1. **前往 Zeabur**
   - 訪問 [zeabur.com](https://zeabur.com/)
   - 點擊右上角「登入」
   - 選擇「使用 GitHub 登入」

2. **建立新專案**
   - 登入後點擊「Create Project」(建立專案)
   - 輸入專案名稱,例如: `telegram-ai-bot`
   - 選擇區域: **Taiwan** (台灣) 或 **Hong Kong** (香港)
   - 點擊「Create」

3. **部署服務**
   - 點擊「Add Service」(新增服務)
   - 選擇「Git」
   - 選擇你的 GitHub 專案: `telegram-ai-assistant`
   - Zeabur 會自動偵測到 Dockerfile

4. **設定環境變數**
   - 在服務頁面點擊「Variables」(環境變數)
   - 點擊「Add Variable」新增以下變數:
   
   | 變數名稱 | 說明 | 範例 |
   |---------|------|------|
   | `TELEGRAM_BOT_TOKEN` | Telegram Bot Token | `123456789:ABCdef...` |
   | `OPENAI_API_KEY` | OpenAI API Key | `sk-...` |
   | `WEATHER_API_KEY` | 天氣 API Key (可選) | `abc123...` |
   | `DATABASE_URL` | 資料庫路徑 | `sqlite:///data/assistant.db` |
   | `TIMEZONE` | 時區 | `Asia/Taipei` |

5. **部署**
   - 設定完環境變數後,Zeabur 會自動開始部署
   - 等待 2-3 分鐘
   - 看到綠色的「Running」狀態表示部署成功!

### 步驟 3: 驗證部署

1. **查看日誌**
   - 點擊服務名稱
   - 切換到「Logs」標籤
   - 應該會看到 "✅ Telegram AI 助理已啟動!"

2. **測試機器人**
   - 在 Telegram 搜尋你的機器人
   - 發送 `/start`
   - 應該會收到歡迎訊息!

## 詳細圖文教學

### 1. 登入 Zeabur

![Zeabur 登入頁面]
- 前往 [zeabur.com](https://zeabur.com/)
- 點擊「使用 GitHub 登入」
- 授權 Zeabur 存取你的 GitHub

### 2. 建立專案

![建立專案]
- 點擊「Create Project」
- 專案名稱: `telegram-ai-bot` (可自訂)
- 區域選擇: **Taiwan** (推薦)
- 點擊「Create」

### 3. 新增服務

![新增服務]
- 點擊「Add Service」
- 選擇「Git」
- 連接你的 GitHub 帳號
- 選擇 `telegram-ai-assistant` 專案

### 4. 自動偵測

![自動偵測]
Zeabur 會自動:
- ✅ 偵測到 Dockerfile
- ✅ 選擇正確的建置方式
- ✅ 開始初始建置

### 5. 設定環境變數

![環境變數設定]
- 點擊「Variables」標籤
- 點擊「Add Variable」
- 逐一加入必要的環境變數:
  ```
  TELEGRAM_BOT_TOKEN = 你的_bot_token
  OPENAI_API_KEY = 你的_openai_key
  WEATHER_API_KEY = 你的_weather_key
  ```

### 6. 等待部署

![部署中]
- Zeabur 會自動建置 Docker 映像
- 部署過程約 2-3 分鐘
- 可以在「Logs」查看即時日誌

### 7. 部署成功!

![部署成功]
- 看到綠色的「Running」狀態
- 日誌顯示 "✅ Telegram AI 助理已啟動!"
- 開始使用你的機器人!

## 進階設定

### 持久化儲存 (Persistent Storage)

如果需要保存資料庫:

1. 在服務頁面點擊「Volumes」
2. 點擊「Add Volume」
3. 設定掛載路徑: `/app/data`
4. 資料庫會被持久化保存

### 自動部署

預設情況下,每次 push 到 GitHub main 分支,Zeabur 會自動重新部署:

```bash
# 更新程式碼
git add .
git commit -m "Update features"
git push origin main

# Zeabur 會自動偵測並重新部署!
```

### 監控與日誌

1. **即時日誌**
   - 點擊「Logs」標籤
   - 查看機器人運行狀況
   - 支援日誌搜尋與過濾

2. **資源監控**
   - 點擊「Metrics」標籤
   - 查看 CPU、記憶體使用率
   - 監控網路流量

3. **重啟服務**
   - 點擊右上角的「Restart」
   - 服務會立即重啟

## 費用說明

### 免費方案

Zeabur 提供免費方案,包含:
- ⚡ 500 小時/月執行時間
- 💾 1GB 儲存空間
- 🌐 100GB 流量
- 🔧 無限專案數

對於個人 Telegram 機器人來說,免費方案完全足夠!

### 付費方案

如果需要更多資源:
- 💎 Developer: $5/月
- 🚀 Team: $15/月
- 🏢 Business: 客製化

## 疑難排解

### 問題 1: 部署失敗

**症狀**: 顯示紅色的 "Failed" 狀態

**解決方法**:
1. 檢查「Logs」查看錯誤訊息
2. 確認 Dockerfile 語法正確
3. 確認 requirements.txt 所有套件都能安裝
4. 嘗試「Redeploy」重新部署

### 問題 2: 機器人沒有回應

**症狀**: 機器人已運行但不回應訊息

**解決方法**:
1. 檢查環境變數是否正確設定
2. 確認 `TELEGRAM_BOT_TOKEN` 有效
3. 確認 `OPENAI_API_KEY` 有餘額
4. 查看「Logs」找出錯誤訊息

### 問題 3: 記憶體不足

**症狀**: 服務頻繁重啟,日誌顯示 OOM (Out of Memory)

**解決方法**:
1. 升級到付費方案獲得更多記憶體
2. 優化程式碼減少記憶體使用
3. 清理對話歷史快取

### 問題 4: 資料庫遺失

**症狀**: 重啟後資料消失

**解決方法**:
1. 設定 Persistent Volume (參考上方「持久化儲存」)
2. 定期備份資料庫

## 從其他平台遷移到 Zeabur

### 從 Railway 遷移

1. 匯出環境變數
2. 在 Zeabur 建立新服務
3. 設定相同的環境變數
4. 部署完成!

### 從 Render 遷移

1. 專案結構不變
2. 直接在 Zeabur 部署即可
3. 記得設定環境變數

### 從 Heroku 遷移

1. 移除 Procfile (Zeabur 使用 Dockerfile)
2. 確認有 Dockerfile
3. 其他步驟同上

## 最佳實踐

### 1. 環境變數管理
```bash
# 本地開發使用 .env
# Zeabur 使用環境變數設定
# 永遠不要提交 .env 到 Git!
```

### 2. 日誌監控
```python
# 在程式中加入適當的日誌
import logging
logging.info("重要操作")
logging.error("錯誤訊息")
```

### 3. 優雅關機
```python
# 程式已經處理 SIGTERM 信號
# Zeabur 重啟時會優雅地關閉服務
```

### 4. 資料庫備份
```bash
# 定期手動備份
# 或使用 Zeabur 的快照功能
```

## 更新與維護

### 更新機器人

```bash
# 1. 修改程式碼
git add .
git commit -m "Update feature"
git push origin main

# 2. Zeabur 自動重新部署
# 3. 完成!
```

### 查看部署歷史

1. 在服務頁面點擊「Deployments」
2. 查看所有部署記錄
3. 可以回滾到之前的版本

### 監控 API 用量

1. OpenAI: https://platform.openai.com/usage
2. Weather: https://home.openweathermap.org/usage
3. 定期檢查避免超額

## 支援與協助

### Zeabur 官方資源

- 📚 文件: https://zeabur.com/docs
- 💬 Discord: https://discord.gg/zeabur
- 📧 Email: support@zeabur.com

### 專案相關

- 🐛 回報問題: GitHub Issues
- 💡 功能建議: GitHub Discussions
- 📖 專案文件: README.md

## 總結

Zeabur 提供了最簡單的部署體驗:
1. ✅ 推送程式碼到 GitHub
2. ✅ 連接到 Zeabur
3. ✅ 設定環境變數
4. ✅ 自動部署完成!

整個過程不到 10 分鐘,而且有繁體中文介面支援!

---

**準備好了嗎?** 
👉 [立即前往 Zeabur 部署](https://zeabur.com/) 🚀

祝你部署順利! 🎉
