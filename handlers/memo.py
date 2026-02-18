"""備忘錄 handler — Lumio 記事功能"""
import asyncio
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from database.operations import DatabaseOperations

db_ops = DatabaseOperations()
logger = logging.getLogger(__name__)


async def add_memo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/memo [內容] — 新增備忘錄"""
    user_id = update.effective_user.id
    content = ' '.join(context.args) if context.args else None

    if not content:
        await update.message.reply_text(
            "請提供備忘錄內容，例如:\n"
            "/memo 記得買牛奶"
        )
        return

    if len(content) > 500:
        await update.message.reply_text("備忘錄內容不能超過 500 字元！")
        return

    try:
        memo = await asyncio.to_thread(db_ops.create_memo, user_id, content)
        await update.message.reply_text(
            f"📝 備忘錄已儲存！\n\n"
            f"#{memo.id} {memo.content}\n"
            f"🕐 {memo.created_at.strftime('%m/%d %H:%M')}"
        )
    except Exception:
        logger.exception("add_memo failed: user_id=%s", user_id)
        await update.message.reply_text("儲存備忘錄時發生錯誤，請稍後再試。")


async def list_memos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/memos — 查看所有備忘錄"""
    user_id = update.effective_user.id

    try:
        memos = await asyncio.to_thread(db_ops.get_user_memos, user_id)

        if not memos:
            await update.message.reply_text("目前沒有備忘錄。\n使用 /memo [內容] 來新增！")
            return

        response = "📝 我的備忘錄\n\n"
        for memo in memos:
            response += (
                f"#{memo.id} {memo.content}\n"
                f"   🕐 {memo.created_at.strftime('%m/%d %H:%M')}\n\n"
            )
        response += "輸入 /delmemo [編號] 可刪除備忘錄"

        await update.message.reply_text(response)

    except Exception:
        logger.exception("list_memos failed: user_id=%s", user_id)
        await update.message.reply_text("查詢備忘錄時發生錯誤，請稍後再試。")


async def delete_memo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/delmemo [編號] — 刪除備忘錄"""
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("請提供備忘錄編號，例如: /delmemo 3")
        return

    try:
        memo_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("請輸入有效的數字編號")
        return

    try:
        success = await asyncio.to_thread(db_ops.delete_memo, memo_id, user_id)
        if success:
            await update.message.reply_text(f"✅ 備忘錄 #{memo_id} 已刪除")
        else:
            await update.message.reply_text(f"找不到備忘錄 #{memo_id}，請確認編號是否正確。")
    except Exception:
        logger.exception("delete_memo failed: user_id=%s", user_id)
        await update.message.reply_text("刪除備忘錄時發生錯誤，請稍後再試。")


async def search_memo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/searchmemo [關鍵字] — 搜尋備忘錄"""
    user_id = update.effective_user.id
    keyword = ' '.join(context.args) if context.args else None

    if not keyword:
        await update.message.reply_text("請提供搜尋關鍵字，例如: /searchmemo 牛奶")
        return

    try:
        memos = await asyncio.to_thread(db_ops.search_memos, user_id, keyword)

        if not memos:
            await update.message.reply_text(f"找不到包含「{keyword}」的備忘錄。")
            return

        response = f"📝 搜尋「{keyword}」的結果（{len(memos)} 筆）\n\n"
        for memo in memos:
            response += (
                f"#{memo.id} {memo.content}\n"
                f"   🕐 {memo.created_at.strftime('%m/%d %H:%M')}\n\n"
            )
        await update.message.reply_text(response)

    except Exception:
        logger.exception("search_memo failed: user_id=%s", user_id)
        await update.message.reply_text("搜尋備忘錄時發生錯誤，請稍後再試。")


async def natural_memo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理自然語言備忘錄 (例如: '記下明天要買東西')"""
    user_id = update.effective_user.id
    text = update.message.text

    # 移除觸發詞
    content = re.sub(r'^(備忘|記下|筆記|memo)\s*', '', text, flags=re.IGNORECASE).strip()

    if not content or len(content) < 2:
        return

    try:
        memo = await asyncio.to_thread(db_ops.create_memo, user_id, content)
        await update.message.reply_text(
            f"📝 好的，我幫你記下來了！\n\n"
            f"#{memo.id} {memo.content}"
        )
    except Exception:
        logger.exception("natural_memo_handler failed: user_id=%s", user_id)
        await update.message.reply_text("儲存時發生錯誤，請稍後再試。")
