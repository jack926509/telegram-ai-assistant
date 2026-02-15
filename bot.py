#!/usr/bin/env python3
"""
Telegram AI 智能助理
整合 OpenAI、行事曆、記帳、搜尋、天氣、股票等功能
"""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

import config
from database.models import init_db
from utils.scheduler import SchedulerManager
from utils.openai_helper import OpenAIHelper

# 匯入各功能處理器
from handlers.calendar import calendar_handler
from handlers.expense import expense_handler, set_budget_handler
from handlers.search import search_handler, summarize_url_handler, quick_search_handler
from handlers.weather import weather_handler, forecast_handler
from handlers.stock import stock_handler, stock_chart_handler, watchlist_handler

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# OpenAI 輔助工具
ai_helper = OpenAIHelper()

# 對話歷史記錄 (簡單實作,實際應該存資料庫)
conversation_history = {}

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 指令"""
    user = update.effective_user
    welcome_message = f"""
👋 你好 {user.first_name}!

我是你的 AI 智能助理,可以幫你:

📅 *行事曆管理*
   • 創建行程: "明天下午3點開會"
   • 查詢行程: "本週的行程"
   • 刪除行程: "刪除明天的會議"

💰 *記帳功能*
   • 記錄支出: "午餐 150 元"
   • 記錄收入: "收入 30000 薪水"
   • 查詢支出: "今天花了多少"
   • 月度報表: "本月支出"

🔍 *網頁搜尋*
   • /search [關鍵字] - 搜尋網頁
   • /summarize [網址] - 總結網頁內容

🌤 *天氣查詢*
   • /weather [城市] - 查詢天氣
   • /forecast [城市] - 未來預報

📈 *股價查詢*
   • /stock [代碼] - 查詢股價
   • /watchlist - 熱門股票

⚙️ *設定*
   • /setbudget [金額] - 設定月度預算
   • /help - 顯示幫助訊息

直接發送訊息就能開始對話! 💬
"""
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown'
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 指令"""
    help_text = """
🤖 *指令列表*

*行事曆相關:*
直接說出你的需求即可,例如:
• "明天下午3點開會"
• "本週有什麼行程"
• "刪除明天的會議"

*記帳相關:*
• "午餐 150 元"
• "收入 30000 薪水"
• "今天花了多少"
• "本月支出"
• /setbudget [金額] - 設定預算

*搜尋相關:*
• /search [關鍵字] - 網頁搜尋
• /summarize [網址] - 總結網頁

*天氣相關:*
• /weather [城市] - 即時天氣
• /forecast [城市] - 未來預報

*股票相關:*
• /stock [代碼] - 查詢股價
• /chart [代碼] - 走勢圖
• /watchlist - 熱門股票

*其他:*
• /help - 顯示此訊息
• /start - 重新開始

💡 *提示*: 直接跟我聊天,我會智能判斷你的需求!
"""
    
    await update.message.reply_text(
        help_text,
        parse_mode='Markdown'
    )

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般訊息"""
    user_id = update.effective_user.id
    message_text = update.message.text.lower()
    
    # 判斷訊息類型並路由到對應的處理器
    
    # 行事曆相關關鍵字
    calendar_keywords = ['行程', '會議', '約', '提醒', '明天', '下週', '月', '日']
    if any(keyword in message_text for keyword in calendar_keywords):
        if any(word in message_text for word in ['查', '看', '有什麼', '什麼時候']):
            await calendar_handler(update, context)
            return
        elif any(word in message_text for word in ['刪', '取消', '不去']):
            await calendar_handler(update, context)
            return
        elif '點' in message_text or '時' in message_text:
            await calendar_handler(update, context)
            return
    
    # 記帳相關關鍵字
    expense_keywords = ['花', '支出', '收入', '薪水', '元', '塊', '錢', '記帳']
    if any(keyword in message_text for keyword in expense_keywords):
        if any(word in message_text for word in ['多少', '總共', '統計', '查詢', '本月', '今天']):
            await expense_handler(update, context)
            return
        elif any(char.isdigit() for char in message_text):
            await expense_handler(update, context)
            return
    
    # 搜尋相關關鍵字
    search_keywords = ['搜尋', '查詢', '找', '搜', 'search']
    if any(keyword in message_text for keyword in search_keywords):
        await quick_search_handler(update, context)
        return
    
    # 天氣相關關鍵字
    weather_keywords = ['天氣', '氣溫', '下雨', '溫度', 'weather']
    if any(keyword in message_text for keyword in weather_keywords):
        # 提取城市名稱
        city = message_text.replace('天氣', '').replace('氣溫', '').replace('weather', '').strip()
        if not city:
            city = '台北'
        context.args = [city]
        await weather_handler(update, context)
        return
    
    # 股票相關關鍵字
    stock_keywords = ['股票', '股價', '大盤', 'stock']
    if any(keyword in message_text for keyword in stock_keywords):
        # 提取股票代碼
        words = message_text.split()
        for word in words:
            if word.isdigit() or word.isupper():
                context.args = [word]
                await stock_handler(update, context)
                return
    
    # 一般對話 - 使用 OpenAI
    await general_chat_handler(update, context)

async def general_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般對話"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # 取得對話歷史
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    
    # 加入使用者訊息
    conversation_history[user_id].append({
        "role": "user",
        "content": message_text
    })
    
    # 保持歷史記錄在合理長度
    if len(conversation_history[user_id]) > 20:
        conversation_history[user_id] = conversation_history[user_id][-20:]
    
    # 發送 "正在輸入" 指示
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )
    
    # 使用 OpenAI 生成回應
    response = ai_helper.general_chat(
        message_text,
        conversation_history.get(user_id)
    )
    
    # 加入助理回應到歷史
    conversation_history[user_id].append({
        "role": "assistant",
        "content": response
    })
    
    await update.message.reply_text(response)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理錯誤"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "抱歉,處理您的請求時發生錯誤。請稍後再試。"
        )

def main():
    """主程式"""
    try:
        # 驗證設定
        config.validate_config()
        
        # 初始化資料庫
        init_db()
        
        # 建立應用程式
        application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # 註冊指令處理器
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        
        # 記帳
        application.add_handler(CommandHandler("setbudget", set_budget_handler))
        
        # 搜尋
        application.add_handler(CommandHandler("search", search_handler))
        application.add_handler(CommandHandler("summarize", summarize_url_handler))
        
        # 天氣
        application.add_handler(CommandHandler("weather", weather_handler))
        application.add_handler(CommandHandler("forecast", forecast_handler))
        
        # 股票
        application.add_handler(CommandHandler("stock", stock_handler))
        application.add_handler(CommandHandler("chart", stock_chart_handler))
        application.add_handler(CommandHandler("watchlist", watchlist_handler))
        
        # 一般訊息處理器
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )
        
        # 錯誤處理器
        application.add_error_handler(error_handler)
        
        # 啟動排程系統
        scheduler = SchedulerManager(application.bot)
        scheduler.start()
        
        # 啟動機器人
        logger.info("🤖 機器人啟動中...")
        print("=" * 50)
        print("✅ Telegram AI 助理已啟動!")
        print("=" * 50)
        
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    
    except KeyboardInterrupt:
        logger.info("機器人正在關閉...")
        print("\n👋 機器人已停止")
    
    except Exception as e:
        logger.error(f"啟動失敗: {e}")
        print(f"❌ 啟動失敗: {e}")
        print("\n請檢查:")
        print("1. .env 檔案是否正確設定")
        print("2. TELEGRAM_BOT_TOKEN 是否有效")
        print("3. OPENAI_API_KEY 是否有效")

if __name__ == '__main__':
    main()
