from contextlib import contextmanager
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from database.models import CalendarEvent, ConversationHistory, Expense, Memo, Reminder, TodoItem, UserPreference, get_db
import config


@contextmanager
def _db_session():
    """統一管理 DB session 的 context manager，確保 session 一定被關閉"""
    db = get_db()
    try:
        yield db
    finally:
        db.close()


class DatabaseOperations:
    """資料庫操作類別"""

    # ========== 行事曆相關操作 ==========

    @staticmethod
    def create_event(user_id, title, start_time, description=None, end_time=None, reminder_time=None):
        """建立行事曆事件"""
        with _db_session() as db:
            event = CalendarEvent(
                user_id=user_id,
                title=title,
                description=description,
                start_time=start_time,
                end_time=end_time,
                reminder_time=reminder_time
            )
            db.add(event)
            db.commit()
            db.refresh(event)
            return event

    @staticmethod
    def get_user_events(user_id, start_date=None, end_date=None):
        """取得使用者的行事曆事件"""
        with _db_session() as db:
            query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id)
            if start_date:
                query = query.filter(CalendarEvent.start_time >= start_date)
            if end_date:
                query = query.filter(CalendarEvent.start_time <= end_date)
            return query.order_by(CalendarEvent.start_time).all()

    @staticmethod
    def update_event(event_id, user_id, **kwargs):
        """更新行事曆事件（需驗證 user_id 所有權）"""
        with _db_session() as db:
            event = db.query(CalendarEvent).filter(
                CalendarEvent.id == event_id,
                CalendarEvent.user_id == user_id
            ).first()
            if event:
                for key, value in kwargs.items():
                    if hasattr(event, key):
                        setattr(event, key, value)
                event.updated_at = datetime.now()
                db.commit()
                db.refresh(event)
                return event
            return None

    @staticmethod
    def delete_event(event_id, user_id):
        """刪除行事曆事件"""
        with _db_session() as db:
            event = db.query(CalendarEvent).filter(
                CalendarEvent.id == event_id,
                CalendarEvent.user_id == user_id
            ).first()
            if event:
                db.delete(event)
                db.commit()
                return True
            return False

    @staticmethod
    def get_pending_reminders():
        """取得待提醒的事件"""
        with _db_session() as db:
            now = datetime.now()
            return db.query(CalendarEvent).filter(
                CalendarEvent.reminder_time <= now,
                CalendarEvent.is_reminded.is_(False),
                CalendarEvent.start_time > now
            ).all()

    @staticmethod
    def mark_as_reminded(event_id):
        """標記事件已提醒"""
        with _db_session() as db:
            event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
            if event:
                event.is_reminded = True
                db.commit()
                return True
            return False

    # ========== 記帳相關操作 ==========

    @staticmethod
    def create_expense(user_id, amount, transaction_type, category=None, description=None, date=None):
        """建立支出/收入記錄"""
        with _db_session() as db:
            expense = Expense(
                user_id=user_id,
                amount=amount,
                category=category,
                description=description,
                transaction_type=transaction_type,
                date=date or datetime.now()
            )
            db.add(expense)
            db.commit()
            db.refresh(expense)
            return expense

    @staticmethod
    def get_user_expenses(user_id, start_date=None, end_date=None, transaction_type=None):
        """取得使用者的支出/收入記錄"""
        with _db_session() as db:
            query = db.query(Expense).filter(Expense.user_id == user_id)
            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)
            if transaction_type:
                query = query.filter(Expense.transaction_type == transaction_type)
            return query.order_by(Expense.date.desc()).all()

    @staticmethod
    def get_daily_summary(user_id, date=None):
        """取得每日支出總結"""
        with _db_session() as db:
            target_date = date or datetime.now()
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)

            expense_total = db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user_id,
                Expense.transaction_type == 'expense',
                Expense.date >= start_of_day,
                Expense.date < end_of_day
            ).scalar() or 0

            income_total = db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user_id,
                Expense.transaction_type == 'income',
                Expense.date >= start_of_day,
                Expense.date < end_of_day
            ).scalar() or 0

            return {
                'date': target_date,
                'expense': expense_total,
                'income': income_total,
                'net': income_total - expense_total
            }

    @staticmethod
    def get_monthly_summary(user_id, year=None, month=None):
        """取得月度支出總結"""
        with _db_session() as db:
            target_date = datetime.now()
            target_year = year or target_date.year
            target_month = month or target_date.month

            expense_total = db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user_id,
                Expense.transaction_type == 'expense',
                extract('year', Expense.date) == target_year,
                extract('month', Expense.date) == target_month
            ).scalar() or 0

            income_total = db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user_id,
                Expense.transaction_type == 'income',
                extract('year', Expense.date) == target_year,
                extract('month', Expense.date) == target_month
            ).scalar() or 0

            category_stats = db.query(
                Expense.category,
                func.sum(Expense.amount).label('total')
            ).filter(
                Expense.user_id == user_id,
                Expense.transaction_type == 'expense',
                extract('year', Expense.date) == target_year,
                extract('month', Expense.date) == target_month
            ).group_by(Expense.category).all()

            return {
                'year': target_year,
                'month': target_month,
                'expense': expense_total,
                'income': income_total,
                'net': income_total - expense_total,
                'categories': {cat: float(total) for cat, total in category_stats if cat}
            }

    # ========== 使用者偏好設定操作 ==========

    @staticmethod
    def get_or_create_user_preference(user_id):
        """取得或建立使用者偏好設定"""
        with _db_session() as db:
            preference = db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).first()
            if not preference:
                preference = UserPreference(user_id=user_id)
                db.add(preference)
                db.commit()
                db.refresh(preference)
            return preference

    @staticmethod
    def update_user_preference(user_id, **kwargs):
        """更新使用者偏好設定"""
        with _db_session() as db:
            preference = db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).first()
            if not preference:
                preference = UserPreference(user_id=user_id)
                db.add(preference)
            for key, value in kwargs.items():
                if hasattr(preference, key):
                    setattr(preference, key, value)
            preference.updated_at = datetime.now()
            db.commit()
            db.refresh(preference)
            return preference

    @staticmethod
    def get_all_users_with_reminders():
        """取得所有啟用提醒的使用者"""
        with _db_session() as db:
            return db.query(UserPreference).filter(
                UserPreference.reminder_enabled.is_(True)
            ).all()

    # ========== 對話歷史操作 ==========

    @staticmethod
    def get_conversation_history(user_id, limit=None):
        """取得使用者的對話歷史"""
        if limit is None:
            limit = config.CONVERSATION_HISTORY_LIMIT
        with _db_session() as db:
            records = (
                db.query(ConversationHistory)
                .filter(ConversationHistory.user_id == user_id)
                .order_by(ConversationHistory.created_at.desc())
                .limit(limit)
                .all()
            )
            return list(reversed(records))

    @staticmethod
    def add_conversation_message(user_id, role, content):
        """新增對話訊息，並自動清理過舊記錄"""
        with _db_session() as db:
            msg = ConversationHistory(user_id=user_id, role=role, content=content)
            db.add(msg)
            db.commit()

            # 保留最近 CONVERSATION_HISTORY_LIMIT * 2 筆，防止無限增長
            keep = config.CONVERSATION_HISTORY_LIMIT * 2
            count = db.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id
            ).count()
            if count > keep:
                oldest = (
                    db.query(ConversationHistory)
                    .filter(ConversationHistory.user_id == user_id)
                    .order_by(ConversationHistory.created_at.asc())
                    .limit(count - keep)
                    .all()
                )
                for old in oldest:
                    db.delete(old)
                db.commit()

    @staticmethod
    def clear_conversation_history(user_id):
        """清除使用者的所有對話歷史"""
        with _db_session() as db:
            db.query(ConversationHistory).filter(
                ConversationHistory.user_id == user_id
            ).delete()
            db.commit()

    # ========== 備忘錄操作 ==========

    @staticmethod
    def create_memo(user_id, content):
        """新增備忘錄"""
        with _db_session() as db:
            memo = Memo(user_id=user_id, content=content)
            db.add(memo)
            db.commit()
            db.refresh(memo)
            return memo

    @staticmethod
    def get_user_memos(user_id, limit=20):
        """取得使用者的備忘錄列表"""
        with _db_session() as db:
            return (
                db.query(Memo)
                .filter(Memo.user_id == user_id)
                .order_by(Memo.created_at.desc())
                .limit(limit)
                .all()
            )

    @staticmethod
    def delete_memo(memo_id, user_id):
        """刪除備忘錄（驗證所有權）"""
        with _db_session() as db:
            memo = db.query(Memo).filter(
                Memo.id == memo_id,
                Memo.user_id == user_id
            ).first()
            if memo:
                db.delete(memo)
                db.commit()
                return True
            return False

    # ========== 待辦清單操作 ==========

    @staticmethod
    def create_todo(user_id, content, due_date=None):
        """新增待辦事項"""
        with _db_session() as db:
            item = TodoItem(user_id=user_id, content=content, due_date=due_date)
            db.add(item)
            db.commit()
            db.refresh(item)
            return item

    @staticmethod
    def get_user_todos(user_id, include_done=False):
        """取得使用者的待辦清單"""
        with _db_session() as db:
            query = db.query(TodoItem).filter(TodoItem.user_id == user_id)
            if not include_done:
                query = query.filter(TodoItem.is_done.is_(False))
            return query.order_by(TodoItem.created_at.asc()).all()

    @staticmethod
    def complete_todo(todo_id, user_id):
        """標記待辦事項為完成"""
        with _db_session() as db:
            item = db.query(TodoItem).filter(
                TodoItem.id == todo_id,
                TodoItem.user_id == user_id
            ).first()
            if item:
                item.is_done = True
                item.done_at = datetime.now()
                db.commit()
                return True
            return False

    @staticmethod
    def delete_todo(todo_id, user_id):
        """刪除待辦事項"""
        with _db_session() as db:
            item = db.query(TodoItem).filter(
                TodoItem.id == todo_id,
                TodoItem.user_id == user_id
            ).first()
            if item:
                db.delete(item)
                db.commit()
                return True
            return False

    @staticmethod
    def get_overdue_todos(user_id):
        """取得已逾期的待辦事項"""
        with _db_session() as db:
            now = datetime.now()
            return (
                db.query(TodoItem)
                .filter(
                    TodoItem.user_id == user_id,
                    TodoItem.is_done.is_(False),
                    TodoItem.due_date < now,
                    TodoItem.due_date.isnot(None)
                )
                .order_by(TodoItem.due_date.asc())
                .all()
            )

    # ========== 搜尋操作 ==========

    @staticmethod
    def search_memos(user_id, keyword, limit=10):
        """關鍵字搜尋備忘錄"""
        with _db_session() as db:
            return (
                db.query(Memo)
                .filter(
                    Memo.user_id == user_id,
                    Memo.content.ilike(f'%{keyword}%')
                )
                .order_by(Memo.created_at.desc())
                .limit(limit)
                .all()
            )

    @staticmethod
    def search_todos(user_id, keyword, include_done=False, limit=10):
        """關鍵字搜尋待辦事項"""
        with _db_session() as db:
            query = db.query(TodoItem).filter(
                TodoItem.user_id == user_id,
                TodoItem.content.ilike(f'%{keyword}%')
            )
            if not include_done:
                query = query.filter(TodoItem.is_done.is_(False))
            return query.order_by(TodoItem.created_at.asc()).limit(limit).all()

    # ========== 快速提醒操作 ==========

    @staticmethod
    def create_reminder(user_id, message, remind_at):
        """新增快速提醒"""
        with _db_session() as db:
            reminder = Reminder(user_id=user_id, message=message, remind_at=remind_at)
            db.add(reminder)
            db.commit()
            db.refresh(reminder)
            return reminder

    @staticmethod
    def get_pending_quick_reminders():
        """取得所有到期待觸發的提醒"""
        with _db_session() as db:
            now = datetime.now()
            return db.query(Reminder).filter(
                Reminder.remind_at <= now,
                Reminder.is_fired.is_(False)
            ).all()

    @staticmethod
    def mark_reminder_fired(reminder_id):
        """標記提醒已發送"""
        with _db_session() as db:
            r = db.query(Reminder).filter(Reminder.id == reminder_id).first()
            if r:
                r.is_fired = True
                db.commit()
                return True
            return False

    @staticmethod
    def get_user_reminders(user_id):
        """取得使用者所有未觸發的提醒"""
        with _db_session() as db:
            now = datetime.now()
            return (
                db.query(Reminder)
                .filter(
                    Reminder.user_id == user_id,
                    Reminder.is_fired.is_(False),
                    Reminder.remind_at > now
                )
                .order_by(Reminder.remind_at.asc())
                .all()
            )

    @staticmethod
    def delete_reminder(reminder_id, user_id):
        """刪除提醒（驗證所有權）"""
        with _db_session() as db:
            r = db.query(Reminder).filter(
                Reminder.id == reminder_id,
                Reminder.user_id == user_id
            ).first()
            if r:
                db.delete(r)
                db.commit()
                return True
            return False
