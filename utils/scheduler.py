import asyncio
import logging
from datetime import datetime, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
from database.operations import DatabaseOperations

logger = logging.getLogger(__name__)


class SchedulerManager:
    """排程管理器"""
    
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=pytz.timezone(config.TIMEZONE))
        self.db_ops = DatabaseOperations()
    
    def start(self):
        """啟動排程器並註冊所有排程任務"""
        # 每分鐘檢查待提醒的行事曆事件
        self.scheduler.add_job(
            self.check_event_reminders,
            'cron',
            minute='*',
            id='event_reminders'
        )

        # 每分鐘檢查快速提醒 (remind.py 建立的一次性提醒)
        self.scheduler.add_job(
            self.check_quick_reminders,
            'cron',
            minute='*',
            id='quick_reminders'
        )

        # 晨間簡報（預設早上 8:00）
        self.scheduler.add_job(
            self.send_morning_briefing,
            'cron',
            hour=config.MORNING_BRIEFING_HOUR,
            minute=config.MORNING_BRIEFING_MINUTE,
            id='morning_briefing'
        )

        # 每日財務報告（預設晚上 8:00）
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
    
    # ── 事件提醒 ─────────────────────────────────────────

    async def check_event_reminders(self):
        """檢查並發送事件提醒"""
        try:
            pending_events = await asyncio.to_thread(self.db_ops.get_pending_reminders)

            for event in pending_events:
                try:
                    time_until = event.start_time - datetime.now()
                    minutes_until = max(0, int(time_until.total_seconds() / 60))

                    message = (
                        f"⏰ 行程提醒\n\n"
                        f"📅 {event.title}\n"
                        f"🕐 開始時間: {event.start_time.strftime('%Y-%m-%d %H:%M')}\n"
                        f"⏱ {minutes_until} 分鐘後開始\n"
                    )

                    if event.description:
                        message += f"📝 {event.description}\n"

                    await self.bot.send_message(chat_id=event.user_id, text=message)
                    await asyncio.to_thread(self.db_ops.mark_as_reminded, event.id)

                except Exception:
                    logger.exception("發送行程提醒失敗: event_id=%s", event.id)

        except Exception:
            logger.exception("check_event_reminders 執行失敗")

    # ── 快速提醒 ─────────────────────────────────────────

    async def check_quick_reminders(self):
        """檢查並發送快速提醒（由 /remind 指令建立）"""
        try:
            pending = await asyncio.to_thread(self.db_ops.get_pending_quick_reminders)
            for reminder in pending:
                try:
                    await self.bot.send_message(
                        chat_id=reminder.user_id,
                        text=f"⏰ 提醒\n\n{reminder.message}"
                    )
                    await asyncio.to_thread(self.db_ops.mark_reminder_fired, reminder.id)
                except Exception:
                    logger.exception("發送快速提醒失敗: reminder_id=%s", reminder.id)
        except Exception:
            logger.exception("check_quick_reminders 執行失敗")

    # ── 晨間簡報 ─────────────────────────────────────────

    async def send_morning_briefing(self):
        """每天早上推送今日行程 + 待辦清單 + 昨日支出摘要"""
        try:
            users = await asyncio.to_thread(self.db_ops.get_all_users_with_reminders)

            for user in users:
                try:
                    await self._send_briefing_to_user(user)
                except Exception:
                    logger.exception("晨間簡報失敗: user_id=%s", user.user_id)

        except Exception:
            logger.exception("send_morning_briefing 執行失敗")

    async def _send_briefing_to_user(self, user):
        """組合並發送單一使用者的晨間簡報"""
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)
        yesterday_start = today_start - timedelta(days=1)

        events = await asyncio.to_thread(
            self.db_ops.get_user_events, user.user_id, today_start, today_end
        )
        todos = await asyncio.to_thread(
            self.db_ops.get_user_todos, user.user_id, False
        )
        yesterday_summary = await asyncio.to_thread(
            self.db_ops.get_daily_summary, user.user_id, yesterday_start
        )

        lines = [f"早安！☀️ 今天是 {now.strftime('%m/%d')}，來看看今天的安排：\n"]

        if events:
            lines.append(f"📅 *今日行程（{len(events)} 項）*")
            for ev in events:
                lines.append(f"  • {ev.start_time.strftime('%H:%M')} {ev.title}")
        else:
            lines.append("📅 今天沒有行程，好好放鬆！")

        overdue = await asyncio.to_thread(
            self.db_ops.get_overdue_todos, user.user_id
        )

        if todos:
            lines.append(f"\n✅ *待辦事項（{len(todos)} 項待完成）*")
            for item in todos[:5]:
                lines.append(f"  ◻ {item.content}")
            if len(todos) > 5:
                lines.append(f"  ... 還有 {len(todos) - 5} 項")
        else:
            lines.append("\n✅ 待辦清單已清空，讚！")

        if overdue:
            lines.append(f"\n⚠️ *逾期待辦（{len(overdue)} 項）*")
            for item in overdue[:3]:
                lines.append(f"  ‼️ {item.content}（截止 {item.due_date.strftime('%m/%d')}）")
            if len(overdue) > 3:
                lines.append(f"  ... 還有 {len(overdue) - 3} 項逾期")

        if yesterday_summary['expense'] > 0 or yesterday_summary['income'] > 0:
            lines.append(
                f"\n💰 *昨日財務*\n"
                f"  支出 ${yesterday_summary['expense']:,.0f}｜"
                f"收入 ${yesterday_summary['income']:,.0f}"
            )

        if user.monthly_budget:
            monthly = await asyncio.to_thread(
                self.db_ops.get_monthly_summary, user.user_id
            )
            ratio = monthly['expense'] / user.monthly_budget if user.monthly_budget else 0
            used_pct = ratio * 100
            if ratio >= 1.0:
                lines.append(
                    f"\n⛔ 月度預算已超支 {used_pct - 100:.1f}%！"
                    f"（${monthly['expense']:,.0f} / ${user.monthly_budget:,.0f}）"
                )
            elif ratio >= config.BUDGET_WARNING_THRESHOLD:
                lines.append(
                    f"\n⚠️ 本月預算已使用 {used_pct:.1f}%"
                    f"（${monthly['expense']:,.0f} / ${user.monthly_budget:,.0f}），注意別超支！"
                )

        await self.bot.send_message(
            chat_id=user.user_id,
            text="\n".join(lines),
            parse_mode='Markdown'
        )
    
    # ── 每日財務報告 ─────────────────────────────────────

    async def send_daily_expense_reminder(self):
        """發送每日支出報告，並主動預警預算超標"""
        try:
            users = await asyncio.to_thread(self.db_ops.get_all_users_with_reminders)

            for user in users:
                try:
                    summary = await asyncio.to_thread(
                        self.db_ops.get_daily_summary, user.user_id
                    )

                    if summary['expense'] == 0 and summary['income'] == 0:
                        continue  # 今天沒有任何記錄，跳過

                    message = (
                        f"📊 今日財務報告\n\n"
                        f"💸 支出: ${summary['expense']:,.0f}\n"
                        f"💵 收入: ${summary['income']:,.0f}\n"
                        f"📈 淨額: ${summary['net']:,.0f}\n"
                    )

                    if user.monthly_budget:
                        monthly = await asyncio.to_thread(
                            self.db_ops.get_monthly_summary, user.user_id
                        )
                        ratio = monthly['expense'] / user.monthly_budget
                        used_pct = ratio * 100

                        if ratio >= 1.0:
                            message += (
                                f"\n⛔ 本月已超支！"
                                f"（${monthly['expense']:,.0f} / ${user.monthly_budget:,.0f}）"
                            )
                        elif ratio >= config.BUDGET_WARNING_THRESHOLD:
                            message += (
                                f"\n⚠️ 預算預警：本月已使用 {used_pct:.1f}%"
                                f"（${monthly['expense']:,.0f} / ${user.monthly_budget:,.0f}），"
                                f"剩餘 ${user.monthly_budget - monthly['expense']:,.0f}"
                            )

                    await self.bot.send_message(chat_id=user.user_id, text=message)

                except Exception:
                    logger.exception("每日財務報告失敗: user_id=%s", user.user_id)

        except Exception:
            logger.exception("send_daily_expense_reminder 執行失敗")
    
    # ── 月度報表 ─────────────────────────────────────────

    async def send_monthly_report(self):
        """月初發送上個月財務報表"""
        try:
            users = await asyncio.to_thread(self.db_ops.get_all_users_with_reminders)

            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            year = last_month.year
            month = last_month.month

            for user in users:
                try:
                    summary = await asyncio.to_thread(
                        self.db_ops.get_monthly_summary,
                        user.user_id,
                        year=year,
                        month=month
                    )

                    message = (
                        f"📊 {year}年{month}月 財務報表\n\n"
                        f"💸 總支出: ${summary['expense']:,.0f}\n"
                        f"💵 總收入: ${summary['income']:,.0f}\n"
                        f"📈 淨額: ${summary['net']:,.0f}\n"
                    )

                    if summary['categories']:
                        message += "\n📋 支出分類 Top 5:\n"
                        for category, amount in sorted(
                            summary['categories'].items(),
                            key=lambda x: x[1],
                            reverse=True
                        )[:5]:
                            pct = (amount / summary['expense'] * 100) if summary['expense'] > 0 else 0
                            message += f"  • {category}: ${amount:,.0f} ({pct:.1f}%)\n"

                    if user.monthly_budget:
                        diff = user.monthly_budget - summary['expense']
                        if diff >= 0:
                            message += f"\n✅ 預算內！剩餘 ${diff:,.0f}"
                        else:
                            message += f"\n⛔ 超支 ${abs(diff):,.0f}"

                    await self.bot.send_message(chat_id=user.user_id, text=message)

                except Exception:
                    logger.exception("月度報表失敗: user_id=%s", user.user_id)

        except Exception:
            logger.exception("send_monthly_report 執行失敗")
    
    def stop(self):
        """停止排程器"""
        self.scheduler.shutdown()
        logger.info("排程系統已停止")
