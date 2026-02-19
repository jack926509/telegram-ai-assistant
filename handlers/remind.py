"""快速提醒 handler — 輕量一次性提醒，無需建立行事曆事件"""
import asyncio
import logging
import re
from datetime import datetime, timedelta

from dateutil import parser as dateparser
from telegram import Update
from telegram.ext import ContextTypes

from database.operations import DatabaseOperations
from utils.time_utils import now_local

db_ops = DatabaseOperations()
logger = logging.getLogger(__name__)

# 相對時間格式：30m / 2h / 1d
_DELTA_RE = re.compile(r'^(\d+)\s*(m|min|h|hr|d|day)s?$', re.IGNORECASE)
# 絕對時間格式：14:30
_TIME_RE = re.compile(r'^(\d{1,2}):(\d{2})$')


def _parse_remind_time(time_str: str) -> datetime | None:
    """將時間字串解析為 naive datetime（與 DB 儲存一致）"""
    now = now_local()

    # 相對時間: 30m / 2h / 1d
    m = _DELTA_RE.match(time_str.strip())
    if m:
        value = int(m.group(1))
        unit = m.group(2).lower()
        if unit in ('m', 'min'):
            result = now + timedelta(minutes=value)
        elif unit in ('h', 'hr'):
            result = now + timedelta(hours=value)
        else:  # d / day
            result = now + timedelta(days=value)
        return result.replace(tzinfo=None)

    # 絕對時間: HH:MM
    m = _TIME_RE.match(time_str.strip())
    if m:
        hour, minute = int(m.group(1)), int(m.group(2))
        target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target <= now:
            target += timedelta(days=1)
        return target.replace(tzinfo=None)

    # 自然語言兜底 (dateutil)
    try:
        parsed = dateparser.parse(time_str)
        if parsed:
            naive = parsed.replace(tzinfo=None)
            if naive > now.replace(tzinfo=None):
                return naive
    except Exception:
        pass

    return None


async def remind_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/remind [時間] [提醒內容] — 設定快速提醒

    時間格式:
      30m / 2h / 1d  →  相對時間
      14:30           →  今日（若已過則明日）同時段
    """
    user_id = update.effective_user.id

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "⏰ 用法: /remind [時間] [提醒內容]\n\n"
            "時間格式:\n"
            "• 30m → 30 分鐘後\n"
            "• 2h  → 2 小時後\n"
            "• 1d  → 明天此時\n"
            "• 14:30 → 今/明天 14:30\n\n"
            "例: /remind 30m 喝水\n"
            "例: /remind 2h 回覆 Email"
        )
        return

    time_str = context.args[0]
    message = ' '.join(context.args[1:])

    if len(message) > 200:
        await update.message.reply_text("提醒訊息不能超過 200 字元！")
        return

    remind_at = _parse_remind_time(time_str)
    if not remind_at:
        await update.message.reply_text(
            f"無法解析時間「{time_str}」\n"
            "請使用: 30m / 2h / 1d / 14:30"
        )
        return

    try:
        reminder = await asyncio.to_thread(db_ops.create_reminder, user_id, message, remind_at)
        await update.message.reply_text(
            f"⏰ 提醒已設定！\n\n"
            f"#{reminder.id} {message}\n"
            f"🕐 {remind_at.strftime('%m/%d %H:%M')}"
        )
    except Exception:
        logger.exception("remind_handler failed: user_id=%s", user_id)
        await update.message.reply_text("設定提醒時發生錯誤，請稍後再試。")


async def list_reminders_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/reminders — 查看所有待提醒的事項"""
    user_id = update.effective_user.id

    try:
        reminders = await asyncio.to_thread(db_ops.get_user_reminders, user_id)

        if not reminders:
            await update.message.reply_text(
                "目前沒有待提醒的事項。\n"
                "使用 /remind [時間] [內容] 來新增！"
            )
            return

        response = f"⏰ 待提醒清單 ({len(reminders)} 項)\n\n"
        for r in reminders:
            response += (
                f"#{r.id} {r.message}\n"
                f"   🕐 {r.remind_at.strftime('%m/%d %H:%M')}\n\n"
            )
        response += "輸入 /delremind [編號] 可取消提醒"
        await update.message.reply_text(response)

    except Exception:
        logger.exception("list_reminders failed: user_id=%s", user_id)
        await update.message.reply_text("查詢提醒時發生錯誤，請稍後再試。")


async def delete_reminder_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/delremind [編號] — 取消提醒"""
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text("請提供提醒編號，例如: /delremind 3")
        return

    try:
        reminder_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("請輸入有效的數字編號")
        return

    try:
        success = await asyncio.to_thread(db_ops.delete_reminder, reminder_id, user_id)
        if success:
            await update.message.reply_text(f"✅ 提醒 #{reminder_id} 已取消")
        else:
            await update.message.reply_text(f"找不到提醒 #{reminder_id}，請確認編號是否正確。")
    except Exception:
        logger.exception("delete_reminder failed: user_id=%s", user_id)
        await update.message.reply_text("取消提醒時發生錯誤，請稍後再試。")
