import asyncio
import logging
from datetime import timedelta

from dateutil import parser
from telegram import Update
from telegram.ext import ContextTypes

from database.operations import DatabaseOperations
from utils.openai_helper import OpenAIHelper
from utils.time_utils import now_local

db_ops = DatabaseOperations()
ai_helper = OpenAIHelper()
logger = logging.getLogger(__name__)


def _find_conflicts(new_start, new_end, existing_events):
    """找出與新行程時段重疊的既有行程清單"""
    conflicts = []
    for ev in existing_events:
        ev_start = ev.start_time
        # 若事件無 end_time，預設持續 1 小時
        ev_end = ev.end_time if ev.end_time else ev_start + timedelta(hours=1)
        # 時間重疊判斷: A.start < B.end AND A.end > B.start
        if new_start < ev_end and new_end > ev_start:
            conflicts.append(ev)
    return conflicts


async def calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """行事曆主處理器"""
    user_id = update.effective_user.id
    message_text = update.message.text

    # 解析使用者意圖 (asyncio.to_thread 避免阻塞 event loop)
    intent_data = await asyncio.to_thread(ai_helper.parse_calendar_intent, message_text)

    if intent_data.get('intent') == 'create':
        await handle_create_event(update, context, user_id, intent_data)

    elif intent_data.get('intent') == 'query':
        await handle_query_events(update, context, user_id, intent_data)

    elif intent_data.get('intent') == 'delete':
        await handle_delete_event(update, context, user_id, intent_data)

    elif intent_data.get('intent') == 'update':
        await handle_update_event(update, context, user_id, intent_data)

    else:
        await update.message.reply_text(
            "我可以幫您:\n"
            "• 建立行程: '明天下午3點開會'\n"
            "• 查詢行程: '本週的行程'\n"
            "• 刪除行程: '刪除明天的會議'\n"
            "• 修改行程: '把明天的會議改到後天下午4點'"
        )


async def handle_create_event(update, context, user_id, intent_data):
    """處理建立行程"""
    try:
        title = intent_data.get('title', '未命名事件')
        description = intent_data.get('description')

        start_time_str = intent_data.get('start_time')
        if not start_time_str:
            await update.message.reply_text("請提供事件時間，例如: '明天下午3點開會'")
            return

        try:
            start_time = parser.parse(start_time_str)
        except Exception:
            await update.message.reply_text("無法解析時間格式，請重新輸入。")
            return

        # 日期合理性驗證：不超過 10 年內、不早於 1 年前
        now_year = now_local().year
        if not (now_year - 1 <= start_time.year <= now_year + 10):
            await update.message.reply_text("請輸入合理的時間範圍（1 年內至未來 10 年）。")
            return

        end_time = None
        if intent_data.get('end_time'):
            try:
                end_time = parser.parse(intent_data['end_time'])
            except Exception:
                pass

        reminder_minutes = intent_data.get('reminder_minutes', 30)
        reminder_time = start_time - timedelta(minutes=reminder_minutes)

        # ── 衝突偵測 ──────────────────────────────────────
        # 新行程若無 end_time，預設持續 1 小時進行衝突比對
        check_end = end_time if end_time else start_time + timedelta(hours=1)
        # 只抓同一天的行程範圍比對即可
        day_start = start_time.replace(hour=0, minute=0, second=0)
        day_end = start_time.replace(hour=23, minute=59, second=59)
        existing = await asyncio.to_thread(
            db_ops.get_user_events, user_id, day_start, day_end
        )
        conflicts = _find_conflicts(start_time, check_end, existing)
        # ─────────────────────────────────────────────────

        event = await asyncio.to_thread(
            db_ops.create_event,
            user_id=user_id,
            title=title,
            start_time=start_time,
            description=description,
            end_time=end_time,
            reminder_time=reminder_time
        )
        
        # 同步至 Google Calendar
        from utils.gcal_helper import sync_event_to_gcal
        gcal_link = await asyncio.to_thread(
            sync_event_to_gcal,
            event.id, event.title, event.start_time, event.end_time, event.description
        )

        response = (
            f"✅ 行程已建立!\n\n"
            f"📅 {event.title}\n"
            f"🕐 {event.start_time.strftime('%Y-%m-%d %H:%M')}\n"
        )

        if event.description:
            response += f"📝 {event.description}\n"

        response += f"⏰ 將在 {reminder_minutes} 分鐘前提醒你"
        
        if gcal_link:
            response += f"\n📅 已同步至 Google 日曆"

        # 若有衝突，附上警告訊息
        if conflicts:
            conflict_names = "、".join(f"「{c.title}」" for c in conflicts[:3])
            response += (
                f"\n\n⚠️ 注意：此時段與 {conflict_names} 有時間衝突，"
                f"請確認行程安排！"
            )

        await update.message.reply_text(response)

    except Exception:
        logger.exception("create event failed: user_id=%s", user_id)
        await update.message.reply_text("建立行程時發生錯誤，請稍後再試。")


async def handle_query_events(update, context, user_id, intent_data):
    """處理查詢行程"""
    try:
        time_range = intent_data.get('time_range', 'week')
        now = now_local()

        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0)
            end_date = now.replace(hour=23, minute=59, second=59)
            title = "今天的行程"
        elif time_range == 'tomorrow':
            tomorrow = now + timedelta(days=1)
            start_date = tomorrow.replace(hour=0, minute=0, second=0)
            end_date = tomorrow.replace(hour=23, minute=59, second=59)
            title = "明天的行程"
        elif time_range == 'month':
            start_date = now
            end_date = now + timedelta(days=30)
            title = "未來一個月的行程"
        else:  # 'week' or default
            start_date = now
            end_date = now + timedelta(days=7)
            title = "未來一週的行程"

        events = await asyncio.to_thread(db_ops.get_user_events, user_id, start_date, end_date)

        if not events:
            await update.message.reply_text(f"{title}目前沒有安排。")
            return

        response = f"📅 {title}:\n\n"
        for event in events:
            response += (
                f"• {event.title}\n"
                f"  🕐 {event.start_time.strftime('%m/%d %H:%M')}\n"
            )
            if event.description:
                response += f"  📝 {event.description}\n"
            response += "\n"

        await update.message.reply_text(response)

    except Exception:
        logger.exception("query event failed: user_id=%s", user_id)
        await update.message.reply_text("查詢行程時發生錯誤，請稍後再試。")


async def handle_delete_event(update, context, user_id, intent_data):
    """處理刪除行程"""
    try:
        keywords = intent_data.get('keywords', '').lower()
        now = now_local()

        events = await asyncio.to_thread(db_ops.get_user_events, user_id, now)

        if not events:
            await update.message.reply_text("目前沒有可刪除的行程。")
            return

        matching_event = None
        for event in events:
            if keywords and keywords in event.title.lower():
                matching_event = event
                break

        if not matching_event:
            response = "請確認要刪除哪個行程:\n\n"
            for i, event in enumerate(events[:5], 1):
                response += f"{i}. {event.title} ({event.start_time.strftime('%m/%d %H:%M')})\n"
            response += "\n請輸入完整行程名稱重新描述"
            await update.message.reply_text(response)
            return

        await asyncio.to_thread(db_ops.delete_event, matching_event.id, user_id)
        
        from utils.gcal_helper import delete_event_from_gcal
        await asyncio.to_thread(delete_event_from_gcal, matching_event.id)
        
        await update.message.reply_text(f"✅ 已刪除行程: {matching_event.title}")

    except Exception:
        logger.exception("delete event failed: user_id=%s", user_id)
        await update.message.reply_text("刪除行程時發生錯誤，請稍後再試。")


async def handle_update_event(update, context, user_id, intent_data):
    """處理修改行程"""
    try:
        keywords = intent_data.get('keywords', '').lower()
        new_start_str = intent_data.get('new_start_time')
        new_end_str = intent_data.get('new_end_time')
        new_title = intent_data.get('new_title')

        if not keywords and not new_title:
            await update.message.reply_text("請說明要修改哪個行程，例如: '把會議改到後天下午3點'")
            return

        now = now_local()
        events = await asyncio.to_thread(db_ops.get_user_events, user_id, now)

        if not events:
            await update.message.reply_text("目前沒有可修改的行程。")
            return

        matching_event = None
        for event in events:
            if keywords and keywords in event.title.lower():
                matching_event = event
                break

        if not matching_event:
            response = "找不到符合的行程，目前的行程:\n\n"
            for i, event in enumerate(events[:5], 1):
                response += f"{i}. {event.title} ({event.start_time.strftime('%m/%d %H:%M')})\n"
            response += "\n請用更明確的名稱描述"
            await update.message.reply_text(response)
            return

        update_kwargs = {}

        if new_start_str:
            try:
                new_start = parser.parse(new_start_str)
                update_kwargs['start_time'] = new_start
                # 同步更新提醒時間
                reminder_minutes = intent_data.get('reminder_minutes', 30)
                update_kwargs['reminder_time'] = new_start - timedelta(minutes=reminder_minutes)
                update_kwargs['is_reminded'] = False  # 重設提醒狀態
            except Exception:
                await update.message.reply_text("無法解析新時間格式，請重新輸入。")
                return

        if new_end_str:
            try:
                update_kwargs['end_time'] = parser.parse(new_end_str)
            except Exception:
                pass

        if new_title:
            update_kwargs['title'] = new_title

        if not update_kwargs:
            await update.message.reply_text("請提供要修改的內容（時間或標題）。")
            return

        updated = await asyncio.to_thread(
            db_ops.update_event, matching_event.id, user_id, **update_kwargs
        )

        if updated:
            from utils.gcal_helper import sync_event_to_gcal
            gcal_link = await asyncio.to_thread(
                sync_event_to_gcal,
                updated.id, updated.title, updated.start_time, updated.end_time, updated.description
            )
            
            response = (
                f"✅ 行程已更新!\n\n"
                f"📅 {updated.title}\n"
                f"🕐 {updated.start_time.strftime('%Y-%m-%d %H:%M')}\n"
            )
            if gcal_link:
                response += f"📅 已同步至 Google 日曆\n"
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("修改失敗，請稍後再試。")

    except Exception:
        logger.exception("update event failed: user_id=%s", user_id)
        await update.message.reply_text("修改行程時發生錯誤，請稍後再試。")
