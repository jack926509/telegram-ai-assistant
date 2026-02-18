"""翻譯 handler — 使用 OpenAI 翻譯任意語言"""
import asyncio
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from utils.openai_helper import OpenAIHelper

ai_helper = OpenAIHelper()
logger = logging.getLogger(__name__)

# 語言代碼對應中文名稱
_LANG_MAP = {
    'en': '英文', 'english': '英文',
    'zh': '繁體中文', 'chinese': '繁體中文', 'tw': '繁體中文',
    'cn': '簡體中文',
    'ja': '日文', 'japanese': '日文',
    'ko': '韓文', 'korean': '韓文',
    'fr': '法文', 'french': '法文',
    'de': '德文', 'german': '德文',
    'es': '西班牙文', 'spanish': '西班牙文',
    'th': '泰文', 'thai': '泰文',
    'vi': '越南文', 'vietnamese': '越南文',
}

# 自然語言觸發 pattern: 翻譯[成/為/into/to] [語言]: [文字]
_NATURAL_RE = re.compile(
    r'(?:翻譯|translate)(?:成|為|into|to)?\s*([^\s:：]+)\s*[:：\s]\s*(.+)',
    re.IGNORECASE | re.DOTALL
)


async def translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/translate [目標語言(可省略)] [文字] — 翻譯文字

    例:
      /translate hello world      → 翻成繁體中文
      /translate en 你好世界       → 翻成英文
      /translate ja 謝謝           → 翻成日文
    """
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "🌐 用法: /translate [目標語言] [文字]\n\n"
            "例:\n"
            "• /translate hello world → 翻成中文\n"
            "• /translate en 你好     → 翻成英文\n"
            "• /translate ja 謝謝     → 翻成日文\n\n"
            "支援語言: en 英 / ja 日 / ko 韓 / fr 法 / de 德 / es 西班牙 / th 泰 / vi 越南"
        )
        return

    first = context.args[0].lower()
    if first in _LANG_MAP:
        target_lang = _LANG_MAP[first]
        text = ' '.join(context.args[1:])
    else:
        target_lang = '繁體中文'
        text = ' '.join(context.args)

    if not text:
        await update.message.reply_text("請提供要翻譯的文字！")
        return

    if len(text) > 1000:
        await update.message.reply_text("翻譯文字不能超過 1000 字元！")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        result = await asyncio.to_thread(ai_helper.translate_text, text, target_lang)
        await update.message.reply_text(f"🌐 翻譯結果（→ {target_lang}）\n\n{result}")
    except Exception:
        logger.exception("translate_handler failed: user_id=%s", user_id)
        await update.message.reply_text("翻譯時發生錯誤，請稍後再試。")


async def natural_translate_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """自然語言觸發翻譯（由 intent_router 路由過來）

    支援格式:
      翻譯成英文: 你好世界
      翻譯 hello
      translate to ja: ありがとう
    """
    user_id = update.effective_user.id
    text = update.message.text

    match = _NATURAL_RE.search(text)
    if match:
        lang_hint = match.group(1).lower()
        content = match.group(2).strip()
        target_lang = _LANG_MAP.get(lang_hint, lang_hint)
    else:
        content = re.sub(r'^(翻譯|translate)\s*', '', text, flags=re.IGNORECASE).strip()
        target_lang = '繁體中文'

    if not content or len(content) < 2:
        return

    if len(content) > 1000:
        await update.message.reply_text("翻譯文字不能超過 1000 字元！")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        result = await asyncio.to_thread(ai_helper.translate_text, content, target_lang)
        await update.message.reply_text(f"🌐 翻譯結果（→ {target_lang}）\n\n{result}")
    except Exception:
        logger.exception("natural_translate failed: user_id=%s", user_id)
        await update.message.reply_text("翻譯時發生錯誤，請稍後再試。")
