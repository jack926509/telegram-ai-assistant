"""圖片分析 handler — 使用 GPT-4o-mini Vision 識圖/OCR"""
import asyncio
import base64
import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.openai_helper import OpenAIHelper

ai_helper = OpenAIHelper()
logger = logging.getLogger(__name__)

# 下載大小上限：5 MB
_MAX_FILE_SIZE = 5 * 1024 * 1024


async def image_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理使用者傳入的圖片

    - 若有 caption，以 caption 作為提問
    - 若無 caption，預設描述圖片並提取文字
    """
    user_id = update.effective_user.id

    # 取最高解析度的版本
    photo = update.message.photo[-1]

    if photo.file_size and photo.file_size > _MAX_FILE_SIZE:
        await update.message.reply_text("圖片太大（超過 5MB），請傳送較小的圖片。")
        return

    prompt = update.message.caption or "請描述這張圖片的內容，並提取其中所有可見的文字。"

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        file = await context.bot.get_file(photo.file_id)
        image_bytes = await file.download_as_bytearray()
        image_b64 = base64.b64encode(bytes(image_bytes)).decode('utf-8')

        result = await asyncio.to_thread(ai_helper.analyze_image, image_b64, prompt)
        await update.message.reply_text(f"🔍 圖片分析\n\n{result}")

    except Exception:
        logger.exception("image_handler failed: user_id=%s", user_id)
        await update.message.reply_text("分析圖片時發生錯誤，請稍後再試。")
