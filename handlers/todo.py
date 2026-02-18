"""待辦清單 handler — Lumio 任務管理功能"""
import asyncio
import logging
import re

from telegram import Update
from telegram.ext import ContextTypes

from database.operations import DatabaseOperations

db_ops = DatabaseOperations()
logger = logging.getLogger(__name__)


async def add_todo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/todo [內容] — 新增待辦事項"""
    user_id = update.effective_user.id
    content = ' '.join(context.args) if context.args else None

    if not content:
        await update.message.reply_text(
            "請提供待辦事項，例如:\n"
            "/todo 準備週報"
        )
        return

    if len(content) > 200:
        await update.message.reply_text("待辦事項不能超過 200 字元！")
        return

    try:
        item = await asyncio.to_thread(db_ops.create_todo, user_id, content)
        pending_count = len(await asyncio.to_thread(db_ops.get_user_todos, user_id))
        await update.message.reply_text(
            f"✅ 待辦事項已新增！\n\n"
            f"#{item.id} {item.content}\n\n"
            f"目前共有 {pending_count} 項待完成"
        )
    except Exception:
        logger.exception("add_todo failed: user_id=%s", user_id)
        await update.message.reply_text("新增待辦事項時發生錯誤，請稍後再試。")


async def list_todos_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/todos — 查看待辦清單"""
    user_id = update.effective_user.id

    try:
        todos = await asyncio.to_thread(db_ops.get_user_todos, user_id, include_done=False)

        if not todos:
            await update.message.reply_text(
                "太棒了！待辦清單已清空！\n"
                "使用 /todo [內容] 新增任務"
            )
            return

        response = f"📋 待辦清單 ({len(todos)} 項)\n\n"
        for item in todos:
            response += (
                f"◻ #{item.id} {item.content}\n"
                f"   🕐 {item.created_at.strftime('%m/%d %H:%M')}\n\n"
            )
        response += "輸入 /done [編號] 標記完成 | /deltodo [編號] 刪除"

        await update.message.reply_text(response)

    except Exception:
        logger.exception("list_todos failed: user_id=%s", user_id)
        await update.message.reply_text("查詢待辦清單時發生錯誤，請稍後再試。")


async def done_todo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/done [編號] — 標記待辦事項為完成"""
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("請提供待辦事項編號，例如: /done 3")
        return

    try:
        todo_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("請輸入有效的數字編號")
        return

    try:
        success = await asyncio.to_thread(db_ops.complete_todo, todo_id, user_id)
        if success:
            await update.message.reply_text(f"完成了！#{todo_id} 已劃掉")
        else:
            await update.message.reply_text(f"找不到待辦事項 #{todo_id}，請確認編號是否正確。")
    except Exception:
        logger.exception("done_todo failed: user_id=%s", user_id)
        await update.message.reply_text("標記完成時發生錯誤，請稍後再試。")


async def delete_todo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/deltodo [編號] — 刪除待辦事項"""
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("請提供待辦事項編號，例如: /deltodo 3")
        return

    try:
        todo_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("請輸入有效的數字編號")
        return

    try:
        success = await asyncio.to_thread(db_ops.delete_todo, todo_id, user_id)
        if success:
            await update.message.reply_text(f"✅ 待辦事項 #{todo_id} 已刪除")
        else:
            await update.message.reply_text(f"找不到待辦事項 #{todo_id}，請確認編號是否正確。")
    except Exception:
        logger.exception("delete_todo failed: user_id=%s", user_id)
        await update.message.reply_text("刪除待辦事項時發生錯誤，請稍後再試。")


async def natural_todo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """處理自然語言待辦清單 (例如: '待辦 準備簡報')"""
    user_id = update.effective_user.id
    text = update.message.text

    content = re.sub(r'^(待辦|todo|任務清單|要做)\s*', '', text, flags=re.IGNORECASE).strip()

    if not content or len(content) < 2:
        await list_todos_handler(update, context)
        return

    try:
        item = await asyncio.to_thread(db_ops.create_todo, user_id, content)
        await update.message.reply_text(
            f"✅ 已加入待辦清單！\n\n"
            f"#{item.id} {item.content}\n\n"
            f"輸入 /todos 查看完整清單"
        )
    except Exception:
        logger.exception("natural_todo_handler failed: user_id=%s", user_id)
        await update.message.reply_text("新增時發生錯誤，請稍後再試。")
