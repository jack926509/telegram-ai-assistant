from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import pytz
import config
from database.operations import DatabaseOperations

class SchedulerManager:
    """排程管理器"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(config.TIMEZONE))
        self.db_ops = DatabaseOperations()
    
    def start(self):
        """啟動排程器"""
        # 每分鐘檢查待提醒的事件
        self.scheduler.add_job(
            self.check_event_reminders,
            'cron',
            minute='*',
            id='event_reminders'
        )
        
        # 每日支出提醒
        self.scheduler.add_job(
            self.send_daily_expense_reminder,
            'cron',
            hour=config.DAILY_REMINDER_HOUR,
            minute=config.DAILY_REMINDER_MINUTE,
            id='daily_expense_reminder'
        )
        
        # 月初發送月度報表
        self.scheduler.add_job(
            self.send_monthly_report,
            'cron',
            day=config.MONTHLY_REPORT_DAY,
            hour=9,
            minute=0,
            id='monthly_report'
        )
        
        self.scheduler.start()
        print("✅ 排程系統啟動成功")
    
    async def check_event_reminders(self):
        """檢查並發送事件提醒"""
        try:
            pending_events = self.db_ops.get_pending_reminders()
            
            for event in pending_events:
                try:
                    # 計算距離事件開始的時間
                    time_until = event.start_time - datetime.now()
                    minutes_until = int(time_until.total_seconds() / 60)
                    
                    message = (
                        f"⏰ 行程提醒\n\n"
                        f"📅 {event.title}\n"
                        f"🕐 開始時間: {event.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                        f"⏱ {minutes_until} 分鐘後開始\n"
                    )
                    
                    if event.description:
                        message += f"📝 {event.description}\n"
                    
                    await self.bot.send_message(
                        chat_id=event.user_id,
                        text=message
                    )
                    
                    # 標記為已提醒
                    self.db_ops.mark_as_reminded(event.id)
                    
                except Exception as e:
                    print(f"發送提醒失敗: {e}")
        
        except Exception as e:
            print(f"檢查提醒失敗: {e}")
    
    async def send_daily_expense_reminder(self):
        """發送每日支出提醒"""
        try:
            users = self.db_ops.get_all_users_with_reminders()
            
            for user in users:
                try:
                    summary = self.db_ops.get_daily_summary(user.user_id)
                    
                    if summary['expense'] > 0 or summary['income'] > 0:
                        message = (
                            f"📊 今日財務報告\n\n"
                            f"💸 支出: ${summary['expense']:,.0f}\n"
                            f"💵 收入: ${summary['income']:,.0f}\n"
                            f"📈 淨額: ${summary['net']:,.0f}\n\n"
                        )
                        
                        # 檢查是否超過預算
                        if user.monthly_budget:
                            current_month = self.db_ops.get_monthly_summary(user.user_id)
                            if current_month['expense'] > user.monthly_budget:
                                message += f"⚠️ 本月已超支 ${current_month['expense'] - user.monthly_budget:,.0f}!\n"
                        
                        await self.bot.send_message(
                            chat_id=user.user_id,
                            text=message
                        )
                
                except Exception as e:
                    print(f"發送每日提醒給用戶 {user.user_id} 失敗: {e}")
        
        except Exception as e:
            print(f"發送每日提醒失敗: {e}")
    
    async def send_monthly_report(self):
        """發送月度報表"""
        try:
            users = self.db_ops.get_all_users_with_reminders()
            
            # 上個月的年月
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            year = last_month.year
            month = last_month.month
            
            for user in users:
                try:
                    summary = self.db_ops.get_monthly_summary(
                        user.user_id,
                        year=year,
                        month=month
                    )
                    
                    message = (
                        f"📊 {year}年{month}月 財務報表\n\n"
                        f"💸 總支出: ${summary['expense']:,.0f}\n"
                        f"💵 總收入: ${summary['income']:,.0f}\n"
                        f"📈 淨額: ${summary['net']:,.0f}\n\n"
                    )
                    
                    if summary['categories']:
                        message += "📋 支出分類:\n"
                        for category, amount in sorted(
                            summary['categories'].items(),
                            key=lambda x: x[1],
                            reverse=True
                        )[:5]:  # 只顯示前5名
                            percentage = (amount / summary['expense'] * 100) if summary['expense'] > 0 else 0
                            message += f"  • {category}: ${amount:,.0f} ({percentage:.1f}%)\n"
                    
                    # 預算比較
                    if user.monthly_budget:
                        diff = user.monthly_budget - summary['expense']
                        if diff >= 0:
                            message += f"\n✅ 預算內! 剩餘 ${diff:,.0f}"
                        else:
                            message += f"\n⚠️ 超支 ${abs(diff):,.0f}"
                    
                    await self.bot.send_message(
                        chat_id=user.user_id,
                        text=message
                    )
                
                except Exception as e:
                    print(f"發送月報給用戶 {user.user_id} 失敗: {e}")
        
        except Exception as e:
            print(f"發送月報失敗: {e}")
    
    def stop(self):
        """停止排程器"""
        self.scheduler.shutdown()
        print("排程系統已停止")
