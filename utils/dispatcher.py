"""
意圖路由分發器 — 供 message_handler 與 voice_handler 共用
避免在 bot.py 與 voice.py 之間產生循環匯入
"""
import asyncio
import logging

import config
from utils.intent_router import route_message

logger = logging.getLogger(__name__)

# 模組層級 singleton（lazy init）
_db_ops = None
_ai_helper = None


def _get_db_ops():
    global _db_ops
    if _db_ops is None:
        from database.operations import DatabaseOperations
        _db_ops = DatabaseOperations()
    return _db_ops


def _get_ai_helper():
    global _ai_helper
    if _ai_helper is None:
        from utils.openai_helper import OpenAIHelper
        _ai_helper = OpenAIHelper()
    return _ai_helper


async def dispatch_text(update, context, text: str):
    """根據意圖路由並呼叫對應 handler"""
    from handlers.calendar import calendar_handler
    from handlers.expense import expense_handler
    from handlers.search import quick_search_handler
    from handlers.weather import weather_handler
    from handlers.memo import natural_memo_handler
    from handlers.todo import natural_todo_handler
    from handlers.translate import natural_translate_handler
    from handlers.exchange import natural_exchange_handler

    routing = await route_message(text)

    # 功能開關檢查
    if routing.intent in config.FEATURES and not config.FEATURES.get(routing.intent, True):
        await _general_chat(update, context, text)
        return

    if routing.intent == "weather":
        context.args = routing.args if routing.args else ["台北"]
        await weather_handler(update, context)
    elif routing.intent == "calendar":
        await calendar_handler(update, context)
    elif routing.intent == "expense":
        await expense_handler(update, context)
    elif routing.intent == "search":
        await quick_search_handler(update, context)
    elif routing.intent == "memo":
        await natural_memo_handler(update, context)
    elif routing.intent == "todo":
        await natural_todo_handler(update, context)
    elif routing.intent == "translate":
        await natural_translate_handler(update, context)
    elif routing.intent == "exchange":
        await natural_exchange_handler(update, context)
    else:
        await _general_chat(update, context, text)


async def _general_chat(update, context, text: str):
    """一般 AI 對話（帶對話歷史）"""
    db_ops = _get_db_ops()
    ai_helper = _get_ai_helper()
    user_id = update.effective_user.id

    history_records = await asyncio.to_thread(db_ops.get_conversation_history, user_id)
    conversation_history = [{"role": r.role, "content": r.content} for r in history_records]

    await asyncio.to_thread(db_ops.add_conversation_message, user_id, "user", text)

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    response = await asyncio.to_thread(
        ai_helper.general_chat,
        text,
        conversation_history
    )

    await asyncio.to_thread(db_ops.add_conversation_message, user_id, "assistant", response)
    await update.message.reply_text(response)
