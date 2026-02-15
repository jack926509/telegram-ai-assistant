from datetime import datetime, timedelta
from sqlalchemy import func, extract
from database.models import CalendarEvent, Expense, UserPreference, get_db


class DatabaseOperations:
    """資料庫操作類別"""
    
    # ========== 行事曆相關操作 ==========
    
    @staticmethod
    def create_event(user_id, title, start_time, description=None, end_time=None, reminder_time=None):
        """建立行事曆事件"""
        db = get_db()
        try:
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
        finally:
            db.close()
    
    @staticmethod
    def get_user_events(user_id, start_date=None, end_date=None):
        """取得使用者的行事曆事件"""
        db = get_db()
        try:
            query = db.query(CalendarEvent).filter(CalendarEvent.user_id == user_id)
            
            if start_date:
                query = query.filter(CalendarEvent.start_time >= start_date)
            if end_date:
                query = query.filter(CalendarEvent.start_time <= end_date)
            
            return query.order_by(CalendarEvent.start_time).all()
        finally:
            db.close()
    
    @staticmethod
    def update_event(event_id, **kwargs):
        """更新行事曆事件"""
        db = get_db()
        try:
            event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
            if event:
                for key, value in kwargs.items():
                    if hasattr(event, key):
                        setattr(event, key, value)
                event.updated_at = datetime.now()
                db.commit()
                db.refresh(event)
                return event
            return None
        finally:
            db.close()
    
    @staticmethod
    def delete_event(event_id, user_id):
        """刪除行事曆事件"""
        db = get_db()
        try:
            event = db.query(CalendarEvent).filter(
                CalendarEvent.id == event_id,
                CalendarEvent.user_id == user_id
            ).first()
            
            if event:
                db.delete(event)
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    @staticmethod
    def get_pending_reminders():
        """取得待提醒的事件"""
        db = get_db()
        try:
            now = datetime.now()
            events = db.query(CalendarEvent).filter(
                CalendarEvent.reminder_time <= now,
                CalendarEvent.is_reminded == False,
                CalendarEvent.start_time > now
            ).all()
            return events
        finally:
            db.close()
    
    @staticmethod
    def mark_as_reminded(event_id):
        """標記事件已提醒"""
        db = get_db()
        try:
            event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
            if event:
                event.is_reminded = True
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    # ========== 記帳相關操作 ==========
    
    @staticmethod
    def create_expense(user_id, amount, transaction_type, category=None, description=None, date=None):
        """建立支出/收入記錄"""
        db = get_db()
        try:
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
        finally:
            db.close()
    
    @staticmethod
    def get_user_expenses(user_id, start_date=None, end_date=None, transaction_type=None):
        """取得使用者的支出/收入記錄"""
        db = get_db()
        try:
            query = db.query(Expense).filter(Expense.user_id == user_id)
            
            if start_date:
                query = query.filter(Expense.date >= start_date)
            if end_date:
                query = query.filter(Expense.date <= end_date)
            if transaction_type:
                query = query.filter(Expense.transaction_type == transaction_type)
            
            return query.order_by(Expense.date.desc()).all()
        finally:
            db.close()
    
    @staticmethod
    def get_daily_summary(user_id, date=None):
        """取得每日支出總結"""
        db = get_db()
        try:
            target_date = date or datetime.now()
            start_of_day = target_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_of_day + timedelta(days=1)
            
            # 支出總計
            expense_total = db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user_id,
                Expense.transaction_type == 'expense',
                Expense.date >= start_of_day,
                Expense.date < end_of_day
            ).scalar() or 0
            
            # 收入總計
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
        finally:
            db.close()
    
    @staticmethod
    def get_monthly_summary(user_id, year=None, month=None):
        """取得月度支出總結"""
        db = get_db()
        try:
            target_date = datetime.now()
            target_year = year or target_date.year
            target_month = month or target_date.month
            
            # 支出總計
            expense_total = db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user_id,
                Expense.transaction_type == 'expense',
                extract('year', Expense.date) == target_year,
                extract('month', Expense.date) == target_month
            ).scalar() or 0
            
            # 收入總計
            income_total = db.query(func.sum(Expense.amount)).filter(
                Expense.user_id == user_id,
                Expense.transaction_type == 'income',
                extract('year', Expense.date) == target_year,
                extract('month', Expense.date) == target_month
            ).scalar() or 0
            
            # 分類統計
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
        finally:
            db.close()
    
    # ========== 使用者偏好設定操作 ==========
    
    @staticmethod
    def get_or_create_user_preference(user_id):
        """取得或建立使用者偏好設定"""
        db = get_db()
        try:
            preference = db.query(UserPreference).filter(
                UserPreference.user_id == user_id
            ).first()
            
            if not preference:
                preference = UserPreference(user_id=user_id)
                db.add(preference)
                db.commit()
                db.refresh(preference)
            
            return preference
        finally:
            db.close()
    
    @staticmethod
    def update_user_preference(user_id, **kwargs):
        """更新使用者偏好設定"""
        db = get_db()
        try:
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
        finally:
            db.close()
    
    @staticmethod
    def get_all_users_with_reminders():
        """取得所有啟用提醒的使用者"""
        db = get_db()
        try:
            users = db.query(UserPreference).filter(
                UserPreference.reminder_enabled == True
            ).all()
            return users
        finally:
            db.close()
