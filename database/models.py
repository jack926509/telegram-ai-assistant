from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

import config
from database.migrations import run_migrations

Base = declarative_base()


class CalendarEvent(Base):
    """行事曆事件模型"""

    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
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

    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, nullable=False, index=True)
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

    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True, nullable=False)
    default_currency = Column(String(10), default="TWD")
    reminder_enabled = Column(Boolean, default=True)
    daily_reminder_time = Column(String(5), default="20:00")
    monthly_budget = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"<UserPreference(user_id={self.user_id})>"


def _engine_options():
    options = {
        "echo": config.DB_ECHO,
        "pool_pre_ping": True,
    }
    if config.DATABASE_URL.startswith("sqlite"):
        options["connect_args"] = {"check_same_thread": False}
    return options


engine = create_engine(config.DATABASE_URL, **_engine_options())
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """取得資料庫 session"""
    return SessionLocal()


def check_db_connection():
    """啟動時檢查資料庫可用性"""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def init_db():
    """初始化資料庫"""
    if config.DB_AUTO_MIGRATE:
        run_migrations(config.DATABASE_URL)
    else:
        Base.metadata.create_all(bind=engine)

    check_db_connection()
    print("✅ 資料庫初始化完成")
