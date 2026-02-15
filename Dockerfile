# 使用 Python 3.11 作為基底映像
FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製需求檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案
COPY . .

# 建立資料目錄
RUN mkdir -p /app/data

# 設定環境變數
ENV PYTHONUNBUFFERED=1

# 執行機器人
CMD ["python", "bot.py"]
