from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime, timedelta
import logging
from dateutil import parser
import pytz
from database.operations import DatabaseOperations
from utils.openai_helper import OpenAIHelper

db_ops = DatabaseOperations()
ai_helper = OpenAIHelper()
logger = logging.getLogger(__name__)

async def calendar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """行事曆主處理器"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # 解析使用者意圖
    intent_data = ai_helper.parse_calendar_intent(message_text)
    
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
            "• 修改行程: '把明天的會議改到後天'"
        )

async def handle_create_event(update, context, user_id, intent_data):
    """處理建立行程"""
    try:
        title = intent_data.get('title', '未命名事件')
        description = intent_data.get('description')
        
        # 解析時間
        start_time_str = intent_data.get('start_time')
        if not start_time_str:
            await update.message.reply_text("請提供事件時間,例如: '明天下午3點開會'")
            return
        
        try:
            start_time = parser.parse(start_time_str)
        except:
            await update.message.reply_text("無法解析時間格式,請重新輸入。")
            return
        
        # 結束時間
        end_time = None
        if intent_data.get('end_time'):
            try:
                end_time = parser.parse(intent_data['end_time'])
            except:
                pass
        
        # 提醒時間
        reminder_minutes = intent_data.get('reminder_minutes', 30)
        reminder_time = start_time - timedelta(minutes=reminder_minutes)
        
        # 建立事件
        event = db_ops.create_event(
            user_id=user_id,
            title=title,
            start_time=start_time,
            description=description,
            end_time=end_time,
            reminder_time=reminder_time
        )
        
        response = (
            f"✅ 行程已建立!\n\n"
            f"📅 {event.title}\n"
            f"🕐 {event.start_time.strftime('%Y-%m-%d %H:%M')}\n"
        )
        
        if event.description:
            response += f"📝 {event.description}\n"
        
        response += f"⏰ 將在 {reminder_minutes} 分鐘前提醒您"
        
        await update.message.reply_text(response)
    
    except Exception:
        logger.exception("create event failed: user_id=%s", user_id)
        await update.message.reply_text(
            "建立行程失敗，可能是資料庫欄位尚未升級。請稍後再試，或通知管理員執行資料庫 migration。"
        )

async def handle_query_events(update, context, user_id, intent_data):
    """處理查詢行程"""
    try:
        time_range = intent_data.get('time_range', 'week')
        now = datetime.now()
        
        # 根據查詢範圍設定日期
        if time_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0)
            end_date = now.replace(hour=23, minute=59, second=59)
            title = "今天的行程"
        elif time_range == 'tomorrow':
            tomorrow = now + timedelta(days=1)
            start_date = tomorrow.replace(hour=0, minute=0, second=0)
            end_date = tomorrow.replace(hour=23, minute=59, second=59)
            title = "明天的行程"
        elif time_range == 'week':
            start_date = now
            end_date = now + timedelta(days=7)
            title = "未來一週的行程"
        elif time_range == 'month':
            start_date = now
            end_date = now + timedelta(days=30)
            title = "未來一個月的行程"
        else:
            start_date = now
            end_date = now + timedelta(days=7)
            title = "未來一週的行程"
        
        events = db_ops.get_user_events(user_id, start_date, end_date)
        
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
        keywords = intent_data.get('keywords', '')
        
        # 查詢最近的事件
        events = db_ops.get_user_events(user_id, datetime.now())
        
        if not events:
            await update.message.reply_text("目前沒有可刪除的行程。")
            return
        
        # 簡單匹配 - 找到包含關鍵字的第一個事件
        matching_event = None
        for event in events:
            if keywords.lower() in event.title.lower():
                matching_event = event
                break
        
        if not matching_event and events:
            # 如果沒有匹配,顯示最近的幾個事件讓使用者選擇
            response = "請確認要刪除哪個行程:\n\n"
            for i, event in enumerate(events[:5], 1):
                response += f"{i}. {event.title} ({event.start_time.strftime('%m/%d %H:%M')})\n"
            response += "\n請輸入編號或重新描述"
            await update.message.reply_text(response)
            return
        
        if matching_event:
            db_ops.delete_event(matching_event.id, user_id)
            await update.message.reply_text(
                f"✅ 已刪除行程: {matching_event.title}"
            )
    
    except Exception:
        logger.exception("delete event failed: user_id=%s", user_id)
        await update.message.reply_text("刪除行程時發生錯誤，請稍後再試。")

async def handle_update_event(update, context, user_id, intent_data):
    """處理修改行程"""
    await update.message.reply_text(
        "修改行程功能開發中。\n"
        "目前請先刪除舊行程,再建立新行程。"
    )
