import json
import logging
from datetime import datetime

import pytz

import config

logger = logging.getLogger(__name__)

# 全域的 Google Calendar API 客戶端
_gcal_service = None

def get_gcal_service():
    """取得 Google Calendar API service instance"""
    global _gcal_service
    if _gcal_service is not None:
        return _gcal_service

    if not config.GOOGLE_CREDENTIALS_JSON or not config.GOOGLE_CALENDAR_ID:
        return None

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        # 支援直接傳入 JSON 字串或檔案路徑
        if config.GOOGLE_CREDENTIALS_JSON.strip().startswith('{'):
            creds_info = json.loads(config.GOOGLE_CREDENTIALS_JSON)
            creds = service_account.Credentials.from_service_account_info(
                creds_info, scopes=['https://www.googleapis.com/auth/calendar']
            )
        else:
            creds = service_account.Credentials.from_service_account_file(
                config.GOOGLE_CREDENTIALS_JSON, scopes=['https://www.googleapis.com/auth/calendar']
            )
            
        _gcal_service = build('calendar', 'v3', credentials=creds)
        return _gcal_service
    except Exception as e:
        logger.error(f"Google Calendar API 授權失敗: {e}")
        return None

def sync_event_to_gcal(event_id, title, start_time, end_time, description):
    """將本地行程同步到 Google Calendar"""
    service = get_gcal_service()
    if not service:
        return None

    try:
        from googleapiclient.errors import HttpError
        
        tz = pytz.timezone(config.TIMEZONE)
        
        def format_rfc3339(dt):
            if dt.tzinfo is None:
                dt = tz.localize(dt)
            return dt.isoformat()

        if not end_time:
            from datetime import timedelta
            end_time = start_time + timedelta(hours=1)

        event = {
            'summary': title,
            'description': description or '',
            'start': {
                'dateTime': format_rfc3339(start_time),
                'timeZone': config.TIMEZONE,
            },
            'end': {
                'dateTime': format_rfc3339(end_time),
                'timeZone': config.TIMEZONE,
            },
            'extendedProperties': {
                'private': {
                    'bot_event_id': str(event_id)
                }
            }
        }

        # 用 private property `bot_event_id` 來尋找是否已經有同步過
        events_result = service.events().list(
            calendarId=config.GOOGLE_CALENDAR_ID,
            privateExtendedProperty=f"bot_event_id={event_id}"
        ).execute()

        existing_events = events_result.get('items', [])

        if existing_events:
            # 已經存在，執行更新
            gcal_event_id = existing_events[0]['id']
            updated_event = service.events().update(
                calendarId=config.GOOGLE_CALENDAR_ID,
                eventId=gcal_event_id,
                body=event
            ).execute()
            logger.info(f"Google Calendar 同步更新成功: {updated_event.get('htmlLink')}")
            return updated_event.get('htmlLink')
        else:
            # 不存在，建立新事件
            created_event = service.events().insert(
                calendarId=config.GOOGLE_CALENDAR_ID, 
                body=event
            ).execute()
            logger.info(f"Google Calendar 同步建立成功: {created_event.get('htmlLink')}")
            return created_event.get('htmlLink')

    except Exception as e:
        logger.error(f"同步行程到 Google Calendar 失敗: {e}", exc_info=True)
        return None

def delete_event_from_gcal(event_id):
    """從 Google Calendar 刪除對應的行程"""
    service = get_gcal_service()
    if not service:
        return False

    try:
        events_result = service.events().list(
            calendarId=config.GOOGLE_CALENDAR_ID,
            privateExtendedProperty=f"bot_event_id={event_id}"
        ).execute()

        existing_events = events_result.get('items', [])
        if existing_events:
            gcal_event_id = existing_events[0]['id']
            service.events().delete(
                calendarId=config.GOOGLE_CALENDAR_ID,
                eventId=gcal_event_id
            ).execute()
            logger.info(f"Google Calendar 同步刪除成功: {gcal_event_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"從 Google Calendar 刪除行程失敗: {e}")
        return False
