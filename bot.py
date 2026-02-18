#!/usr/bin/env python3
"""
Telegram AI 智能助理 — Lumio
整合 OpenAI、行事曆、記帳、搜尋、天氣、股票、備忘錄、待辦清單等功能
"""

import asyncio
import logging
import time
from collections import defaultdict, deque

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
from database.operations import DatabaseOperations
from utils.scheduler import SchedulerManager
from utils.openai_helper import OpenAIHelper
from utils.intent_router import route_message

# 匯入各功能處理器
from handlers.calendar import calendar_handler
from handlers.expense import expense_handler, set_budget_handler
from handlers.search import search_handler, summarize_url_handler, quick_search_handler
from handlers.weather import weather_handler, forecast_handler
from handlers.stock import stock_handler, stock_chart_handler, watchlist_handler
from handlers.memo import add_memo_handler, list_memos_handler, delete_memo_handler, natural_memo_handler
from handlers.todo import add_todo_handler, list_todos_handler, done_todo_handler, delete_todo_handler, natural_todo_handler

# 設定日誌
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# OpenAI 輔助工具
ai_helper = OpenAIHelper()

# 資料庫操作
db_ops = DatabaseOperations()

# ── 速率限制 ──────────────────────────────────────────────
_rate_limit_store: dict[int, deque] = defaultdict(deque)
_RATE_WINDOW = 60  # 秒


def _check_rate_limit(user_id: int) -> bool:
    """回傳 True 表示在速率限制內，False 表示已超限"""
    now = time.monotonic()
    q = _rate_limit_store[user_id]
    while q and q[0] < now - _RATE_WINDOW:
        q.popleft()
    if len(q) >= config.RATE_LIMIT_MAX_MESSAGES:
        return False
    q.append(now)
    return True


# ── 指令處理器 ────────────────────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /start 指令"""
    user = update.effective_user
    name = config.ASSISTANT_NAME
    welcome_message = f"""
嗨 {user.first_name}！我是 *{name}* ✨

你的貼身 AI 女友助手，什麼都難不倒我！

📅 *行事曆*
   • 建立: "明天下午3點開會"
   • 查詢: "本週的行程"
   • 修改: "把會議改到後天下午4點"
   • 刪除: "刪除明天的會議"

💰 *記帳*
   • 記錄: "午餐 150 元" / "收入 30000 薪水"
   • 查詢: "今天花了多少" / "本月支出"
   • /setbudget [金額] - 設定月度預算

📝 *備忘錄*
   • /memo [內容] - 新增備忘錄
   • /memos - 查看所有備忘錄
   • /delmemo [編號] - 刪除備忘錄

✅ *待辦清單*
   • /todo [內容] - 新增待辦事項
   • /todos - 查看清單
   • /done [編號] - 標記完成
   • /deltodo [編號] - 刪除

🔍 *搜尋*
   • /search [關鍵字] - 網頁搜尋
   • /summarize [網址] - 總結網頁

🌤 *天氣*
   • /weather [城市] - 即時天氣
   • /forecast [城市] - 未來預報

📈 *股票*
   • /stock [代碼] - 查詢股價
   • /chart [代碼] - 走勢圖
   • /watchlist - 熱門股票

⚙️ *其他*
   • /newchat - 清除對話記憶，重新開始
   • /help - 查看所有指令

直接跟我說話就好，我會懂你的！💬
"""

    await update.message.reply_text(welcome_message, parse_mode='Markdown')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理 /help 指令"""
    name = config.ASSISTANT_NAME
    help_text = f"""
🤖 *{name} 指令一覽*

*行事曆:*
• "明天下午3點開會" / "本週有什麼行程"
• "把會議改到後天" / "刪除明天的會議"

*記帳:*
• "午餐 150 元" / "收入 30000 薪水"
• "今天花了多少" / "本月支出"
• /setbudget [金額] - 設定預算

*備忘錄:*
• /memo [內容] - 新增
• /memos - 查看
• /delmemo [編號] - 刪除

*待辦清單:*
• /todo [內容] - 新增
• /todos - 查看
• /done [編號] - 完成
• /deltodo [編號] - 刪除

*搜尋:*
• /search [關鍵字] - 網頁搜尋
• /summarize [網址] - 總結網頁

*天氣:*
• /weather [城市] / /forecast [城市]

*股票:*
• /stock [代碼] / /chart [代碼] / /watchlist

*對話:*
• /newchat - 清除對話記憶重新開始
• /help - 顯示此訊息
"""

    await update.message.reply_text(help_text, parse_mode='Markdown')


async def newchat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/newchat — 清除對話歷史，重新開始"""
    user_id = update.effective_user.id
    try:
        await asyncio.to_thread(db_ops.clear_conversation_history, user_id)
        await update.message.reply_text("好的！對話記憶已清除，我們重新開始吧 😊")
    except Exception:
        logger.exception("newchat failed: user_id=%s", user_id)
        await update.message.reply_text("清除失敗，請稍後再試。")


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般訊息"""
    user_id = update.effective_user.id
    message_text_raw = update.message.text or ""

    # 速率限制檢查
    if not _check_rate_limit(user_id):
        await update.message.reply_text(
            f"你傳太快囉！一分鐘最多 {config.RATE_LIMIT_MAX_MESSAGES} 則訊息，讓我喘口氣 😅"
        )
        return

    # 訊息長度限制
    if len(message_text_raw) > config.MESSAGE_MAX_LENGTH:
        await update.message.reply_text(
            f"訊息太長了，請控制在 {config.MESSAGE_MAX_LENGTH} 字以內！"
        )
        return

    routing = await route_message(message_text_raw)

    # 功能開關檢查
    if routing.intent in config.FEATURES and not config.FEATURES.get(routing.intent, True):
        await general_chat_handler(update, context)
        return

    if routing.intent == "calendar":
        await calendar_handler(update, context)
        return

    if routing.intent == "expense":
        await expense_handler(update, context)
        return

    if routing.intent == "search":
        await quick_search_handler(update, context)
        return

    if routing.intent == "weather":
        context.args = routing.args if routing.args else ["台北"]
        await weather_handler(update, context)
        return

    if routing.intent == "stock":
        if routing.args:
            context.args = routing.args
            await stock_handler(update, context)
            return
        await update.message.reply_text("請提供股票代碼，例如：2330 或 AAPL")
        return

    if routing.intent == "memo":
        await natural_memo_handler(update, context)
        return

    if routing.intent == "todo":
        await natural_todo_handler(update, context)
        return

    # 一般對話
    await general_chat_handler(update, context)


async def general_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理一般對話（使用資料庫持久化歷史）"""
    user_id = update.effective_user.id
    message_text = update.message.text

    # 從 DB 取得對話歷史
    history_records = await asyncio.to_thread(db_ops.get_conversation_history, user_id)
    conversation_history = [{"role": r.role, "content": r.content} for r in history_records]

    # 儲存使用者訊息
    await asyncio.to_thread(db_ops.add_conversation_message, user_id, "user", message_text)

    # 發送 "正在輸入" 指示
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    # 使用 OpenAI 生成回應
    response = await asyncio.to_thread(
        ai_helper.general_chat,
        message_text,
        conversation_history
    )

    # 儲存助理回應
    await asyncio.to_thread(db_ops.add_conversation_message, user_id, "assistant", response)

    await update.message.reply_text(response)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理錯誤"""
    logger.error("Update %s caused error %s", update, context.error, exc_info=context.error)

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "哎呀，出了點狀況！請稍後再試一次 😅"
        )


def main():
    """主程式"""
    try:
        config.validate_config()
        init_db()

        application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

        # ── 基本指令 ──
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("newchat", newchat_command))

        # ── 記帳 ──
        application.add_handler(CommandHandler("setbudget", set_budget_handler))

        # ── 搜尋 ──
        application.add_handler(CommandHandler("search", search_handler))
        application.add_handler(CommandHandler("summarize", summarize_url_handler))

        # ── 天氣 ──
        application.add_handler(CommandHandler("weather", weather_handler))
        application.add_handler(CommandHandler("forecast", forecast_handler))

        # ── 股票 ──
        application.add_handler(CommandHandler("stock", stock_handler))
        application.add_handler(CommandHandler("chart", stock_chart_handler))
        application.add_handler(CommandHandler("watchlist", watchlist_handler))

        # ── 備忘錄 ──
        application.add_handler(CommandHandler("memo", add_memo_handler))
        application.add_handler(CommandHandler("memos", list_memos_handler))
        application.add_handler(CommandHandler("delmemo", delete_memo_handler))

        # ── 待辦清單 ──
        application.add_handler(CommandHandler("todo", add_todo_handler))
        application.add_handler(CommandHandler("todos", list_todos_handler))
        application.add_handler(CommandHandler("done", done_todo_handler))
        application.add_handler(CommandHandler("deltodo", delete_todo_handler))

        # ── 一般訊息 ──
        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
        )

        application.add_error_handler(error_handler)

        # 啟動排程系統
        scheduler = SchedulerManager(application.bot)
        scheduler.start()

        logger.info("%s 啟動中...", config.ASSISTANT_NAME)
        print("=" * 50)
        print(f"✅ {config.ASSISTANT_NAME} AI 助理已啟動!")
        print("=" * 50)

        application.run_polling(allowed_updates=Update.ALL_TYPES)

    except KeyboardInterrupt:
        logger.info("機器人正在關閉...")
        print(f"\n👋 {config.ASSISTANT_NAME} 下線了，再見！")

    except Exception as e:
        logger.error("啟動失敗: %s", e)
        print(f"❌ 啟動失敗: {e}")
        print("\n請檢查:")
        print("1. .env 檔案是否正確設定")
        print("2. TELEGRAM_BOT_TOKEN 是否有效")
        print("3. OPENAI_API_KEY 是否有效")


if __name__ == '__main__':
    main()
