"""語音訊息 handler — Whisper 轉文字後路由至各功能"""
import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from utils.openai_helper import OpenAIHelper

ai_helper = OpenAIHelper()
logger = logging.getLogger(__name__)

# 語音長度上限：120 秒
_MAX_DURATION_SECONDS = 120


async def voice_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """將語音訊息轉成文字，再透過 dispatcher 走正常意圖路由"""
    user_id = update.effective_user.id
    voice = update.message.voice

    if voice.duration > _MAX_DURATION_SECONDS:
        await update.message.reply_text(
            f"語音訊息太長（超過 {_MAX_DURATION_SECONDS} 秒），請傳文字訊息。"
        )
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        file = await context.bot.get_file(voice.file_id)
        voice_bytes = await file.download_as_bytearray()

        transcript = await asyncio.to_thread(ai_helper.transcribe_voice, bytes(voice_bytes))

        if not transcript or not transcript.strip():
            await update.message.reply_text("無法辨識語音內容，請再試一次或改用文字訊息。")
            return

        await update.message.reply_text(f"🎤 辨識到：「{transcript}」")

        # 路由至 dispatcher（避免循環匯入，在函式內 lazy import）
        from utils.dispatcher import dispatch_text
        await dispatch_text(update, context, transcript)

    except Exception:
        logger.exception("voice_handler failed: user_id=%s", user_id)
        await update.message.reply_text("處理語音時發生錯誤，請稍後再試。")
