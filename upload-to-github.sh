#!/bin/bash

echo "=========================================="
echo "  GitHub 上傳腳本"
echo "=========================================="
echo ""

# 檢查 Git
if ! command -v git &> /dev/null; then
    echo "❌ 找不到 Git,請先安裝 Git"
    exit 1
fi

echo "請輸入你的 GitHub 使用者名稱:"
read username

echo "請輸入你的專案名稱 (例如: telegram-ai-assistant):"
read repo_name

echo ""
echo "正在初始化 Git 倉庫..."

# 初始化 Git
git init

# 加入所有檔案
git add .

# 第一次提交
git commit -m "Initial commit: Telegram AI Assistant with calendar, expense tracking, search, weather, and stock features"

# 設定遠端倉庫
git branch -M main
git remote add origin "https://github.com/$username/$repo_name.git"

echo ""
echo "=========================================="
echo "  下一步操作:"
echo "=========================================="
echo ""
echo "1. 前往 https://github.com/new 建立新的專案倉庫"
echo "   專案名稱: $repo_name"
echo "   可見性: Public 或 Private"
echo ""
echo "2. 建立完成後,執行以下指令上傳:"
echo ""
echo "   git push -u origin main"
echo ""
echo "3. 如果需要輸入認證,使用 GitHub Personal Access Token"
echo "   取得 Token: https://github.com/settings/tokens"
echo ""
echo "=========================================="
