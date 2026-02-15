#!/bin/bash

echo "=========================================="
echo "  Telegram AI 助理 - 快速啟動腳本"
echo "=========================================="
echo ""

# 檢查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 找不到 Python3,請先安裝 Python 3.9+"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 檢查 .env 檔案
if [ ! -f .env ]; then
    echo "⚠️  找不到 .env 檔案"
    echo "📝 正在建立 .env 檔案..."
    cp .env.example .env
    echo ""
    echo "請編輯 .env 檔案並填入你的 API keys:"
    echo "  - TELEGRAM_BOT_TOKEN"
    echo "  - OPENAI_API_KEY"
    echo "  - WEATHER_API_KEY (可選)"
    echo ""
    echo "編輯完成後,請重新執行此腳本。"
    exit 0
fi

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "📦 建立虛擬環境..."
    python3 -m venv venv
fi

# 啟動虛擬環境
echo "🔧 啟動虛擬環境..."
source venv/bin/activate

# 安裝依賴
echo "📥 安裝依賴套件..."
pip install -q -r requirements.txt

# 建立資料目錄
mkdir -p data

echo ""
echo "=========================================="
echo "  🚀 啟動機器人..."
echo "=========================================="
echo ""

# 執行機器人
python bot.py
