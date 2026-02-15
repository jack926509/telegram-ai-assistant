from telegram import Update
from telegram.ext import ContextTypes
from datetime import datetime
from database.operations import DatabaseOperations
from utils.openai_helper import OpenAIHelper

db_ops = DatabaseOperations()
ai_helper = OpenAIHelper()

async def expense_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """記帳主處理器"""
    user_id = update.effective_user.id
    message_text = update.message.text
    
    # 解析使用者意圖
    intent_data = ai_helper.parse_expense_intent(message_text)
    
    if intent_data.get('intent') == 'record':
        await handle_record_expense(update, context, user_id, intent_data)
    
    elif intent_data.get('intent') == 'query':
        await handle_query_expenses(update, context, user_id, intent_data)
    
    else:
        await update.message.reply_text(
            "我可以幫您:\n"
            "• 記錄支出: '午餐 150 元'\n"
            "• 記錄收入: '收入 30000 薪水'\n"
            "• 查詢支出: '今天花了多少'\n"
            "• 月度報表: '本月支出'"
        )

async def handle_record_expense(update, context, user_id, intent_data):
    """處理記錄支出/收入"""
    try:
        amount = intent_data.get('amount')
        transaction_type = intent_data.get('transaction_type', 'expense')
        category = intent_data.get('category', '其他')
        description = intent_data.get('description', '')
        
        if not amount:
            await update.message.reply_text("請提供金額,例如: '午餐 150 元'")
            return
        
        # 建立記錄
        expense = db_ops.create_expense(
            user_id=user_id,
            amount=float(amount),
            transaction_type=transaction_type,
            category=category,
            description=description
        )
        
        # 取得今日總計
        daily_summary = db_ops.get_daily_summary(user_id)
        
        type_emoji = "💸" if transaction_type == 'expense' else "💵"
        type_text = "支出" if transaction_type == 'expense' else "收入"
        
        response = (
            f"✅ {type_emoji} {type_text}已記錄!\n\n"
            f"金額: ${amount:,.0f}\n"
            f"分類: {category}\n"
        )
        
        if description:
            response += f"說明: {description}\n"
        
        response += (
            f"\n📊 今日統計:\n"
            f"支出: ${daily_summary['expense']:,.0f}\n"
            f"收入: ${daily_summary['income']:,.0f}\n"
            f"淨額: ${daily_summary['net']:,.0f}"
        )
        
        await update.message.reply_text(response)
    
    except Exception as e:
        await update.message.reply_text(f"記錄時發生錯誤: {str(e)}")

async def handle_query_expenses(update, context, user_id, intent_data):
    """處理查詢支出"""
    try:
        time_range = intent_data.get('time_range', 'today')
        
        if time_range == 'today':
            summary = db_ops.get_daily_summary(user_id)
            response = ai_helper.format_expense_summary(summary)
        
        elif time_range == 'month':
            summary = db_ops.get_monthly_summary(user_id)
            response = ai_helper.format_expense_summary(summary)
        
        elif time_range == 'week':
            # 查詢本週
            now = datetime.now()
            start_of_week = now - timedelta(days=now.weekday())
            start_of_week = start_of_week.replace(hour=0, minute=0, second=0)
            
            expenses = db_ops.get_user_expenses(
                user_id,
                start_date=start_of_week,
                transaction_type='expense'
            )
            incomes = db_ops.get_user_expenses(
                user_id,
                start_date=start_of_week,
                transaction_type='income'
            )
            
            total_expense = sum(e.amount for e in expenses)
            total_income = sum(e.amount for e in incomes)
            
            response = (
                f"💰 本週財務總結\n\n"
                f"💸 支出: ${total_expense:,.0f}\n"
                f"💵 收入: ${total_income:,.0f}\n"
                f"📊 淨額: ${total_income - total_expense:,.0f}"
            )
        
        else:
            summary = db_ops.get_daily_summary(user_id)
            response = ai_helper.format_expense_summary(summary)
        
        await update.message.reply_text(response)
    
    except Exception as e:
        await update.message.reply_text(f"查詢時發生錯誤: {str(e)}")

async def set_budget_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """設定月度預算"""
    user_id = update.effective_user.id
    
    try:
        if not context.args or len(context.args) == 0:
            await update.message.reply_text(
                "請提供預算金額,例如: /setbudget 30000"
            )
            return
        
        budget = float(context.args[0])
        
        db_ops.update_user_preference(
            user_id=user_id,
            monthly_budget=budget
        )
        
        await update.message.reply_text(
            f"✅ 已設定月度預算: ${budget:,.0f}"
        )
    
    except ValueError:
        await update.message.reply_text("請輸入有效的數字金額")
    except Exception as e:
        await update.message.reply_text(f"設定預算時發生錯誤: {str(e)}")

from datetime import timedelta
