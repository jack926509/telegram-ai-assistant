from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import config

Base = declarative_base()

class CalendarEvent(Base):
    """行事曆事件模型"""
    __tablename__ = 'calendar_events'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(String(500))
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    reminder_time = Column(DateTime)
    is_reminded = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<CalendarEvent(title='{self.title}', start_time='{self.start_time}')>"


class Expense(Base):
    """支出/收入記錄模型"""
    __tablename__ = 'expenses'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    category = Column(String(50))
    description = Column(String(200))
    transaction_type = Column(String(10), nullable=False)  # 'expense' or 'income'
    date = Column(DateTime, default=datetime.now, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"<Expense(amount={self.amount}, category='{self.category}', type='{self.transaction_type}')>"


class UserPreference(Base):
    """使用者偏好設定模型"""
    __tablename__ = 'user_preferences'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    default_currency = Column(String(10), default='TWD')
    reminder_enabled = Column(Boolean, default=True)
    daily_reminder_time = Column(String(5), default='20:00')
    monthly_budget = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id})>"


# 建立資料庫引擎
engine = create_engine(config.DATABASE_URL, echo=False)

# 建立所有表格
Base.metadata.create_all(engine)

# 建立 Session 工廠
SessionLocal = sessionmaker(bind=engine)

def get_db():
    """取得資料庫 session"""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        db.close()
        raise e

def init_db():
    """初始化資料庫"""
    Base.metadata.create_all(engine)
    print("✅ 資料庫初始化完成")
