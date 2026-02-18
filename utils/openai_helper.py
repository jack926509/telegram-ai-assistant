import json
import re

import openai
from openai import OpenAI

import config

# 初始化 OpenAI 客戶端
client = OpenAI(api_key=config.OPENAI_API_KEY)

# 預編譯 markdown code block 的正規表達式，避免每次呼叫重新編譯
_JSON_CODE_BLOCK_RE = re.compile(r'```(?:json)?\s*([\s\S]+?)\s*```')


def _extract_json(text: str) -> dict:
    """從可能包含 markdown code block 的文字中安全提取 JSON"""
    stripped = text.strip()
    match = _JSON_CODE_BLOCK_RE.search(stripped)
    if match:
        stripped = match.group(1).strip()
    return json.loads(stripped)


class OpenAIHelper:
    """OpenAI API 輔助類別"""

    @staticmethod
    def chat_completion(messages, temperature=0.7, max_tokens=1000):
        """基本對話完成"""
        try:
            response = client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except openai.RateLimitError:
            return "抱歉，目前請求量太高，請稍後再試。"
        except openai.AuthenticationError:
            return "AI 服務驗證失敗，請聯絡管理員。"
        except Exception:
            return "AI 服務暫時無法使用，請稍後再試。"

    @staticmethod
    def parse_calendar_intent(user_message):
        """解析行事曆相關意圖"""
        from utils.time_utils import now_local
        current_time = now_local().strftime('%Y-%m-%d %H:%M')

        system_prompt = f"""你是一個行事曆助理。目前時間為 {current_time}。請分析使用者的訊息並判斷意圖。

回傳純 JSON 格式 (不要加 markdown):
{{
    "intent": "create/query/update/delete",
    "title": "事件標題",
    "description": "詳細描述",
    "start_time": "YYYY-MM-DD HH:MM",
    "end_time": "YYYY-MM-DD HH:MM (可選)",
    "reminder_minutes": 提前提醒分鐘數,
    "keywords": "搜尋關鍵字 (update/delete 時用)",
    "new_start_time": "YYYY-MM-DD HH:MM (update 時用)",
    "new_end_time": "YYYY-MM-DD HH:MM (update 時用，可選)",
    "time_range": "today/tomorrow/week/month (query 時用)"
}}

範例:
輸入: "明天下午3點開會討論專案"
輸出: {{"intent": "create", "title": "開會討論專案", "start_time": "YYYY-MM-DD 15:00", "reminder_minutes": 30}}

輸入: "本週有什麼行程"
輸出: {{"intent": "query", "time_range": "week"}}

輸入: "刪除明天的會議"
輸出: {{"intent": "delete", "keywords": "會議"}}

輸入: "把明天的會議改到後天下午4點"
輸出: {{"intent": "update", "keywords": "會議", "new_start_time": "YYYY-MM-DD 16:00"}}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        try:
            response = OpenAIHelper.chat_completion(messages, temperature=0.1)
            return _extract_json(response)
        except Exception:
            return {"intent": "unknown", "error": "無法解析意圖"}

    @staticmethod
    def parse_expense_intent(user_message):
        """解析記帳相關意圖"""
        system_prompt = """你是一個記帳助理。請分析使用者的訊息並判斷意圖。

回傳純 JSON 格式 (不要加 markdown):
{
    "intent": "record/query",
    "transaction_type": "expense/income",
    "amount": 金額數字,
    "category": "分類(食物/交通/娛樂/購物/醫療/其他/薪水/獎金等)",
    "description": "描述",
    "time_range": "today/week/month (query 時用)"
}

範例:
輸入: "午餐花了150元"
輸出: {"intent": "record", "transaction_type": "expense", "amount": 150, "category": "食物", "description": "午餐"}

輸入: "收入30000薪水"
輸出: {"intent": "record", "transaction_type": "income", "amount": 30000, "category": "薪水", "description": "薪水"}

輸入: "今天花了多少錢"
輸出: {"intent": "query", "time_range": "today"}

輸入: "本月支出"
輸出: {"intent": "query", "time_range": "month"}
"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        try:
            response = OpenAIHelper.chat_completion(messages, temperature=0.1)
            return _extract_json(response)
        except Exception:
            return {"intent": "unknown", "error": "無法解析意圖"}

    @staticmethod
    def summarize_web_content(content, max_length=500):
        """總結網頁內容"""
        system_prompt = f"請用繁體中文總結以下內容，重點摘要不超過{max_length}字。突出最重要的資訊和關鍵點。"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content[:4000]}
        ]

        return OpenAIHelper.chat_completion(messages, temperature=0.5)

    @staticmethod
    def general_chat(user_message, conversation_history=None):
        """一般對話"""
        messages = [{"role": "system", "content": config.ASSISTANT_PERSONA_PROMPT}]

        if conversation_history:
            messages.extend(conversation_history[-10:])

        messages.append({"role": "user", "content": user_message})

        return OpenAIHelper.chat_completion(messages, temperature=0.8)

    @staticmethod
    def format_calendar_response(events):
        """格式化行事曆回應"""
        if not events:
            return "目前沒有行程安排。"

        event_list = "\n\n".join([
            f"📅 {event.title}\n"
            f"⏰ {event.start_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"📝 {event.description or '無描述'}"
            for event in events
        ])

        return f"您的行程如下:\n\n{event_list}"

    @staticmethod
    def format_expense_summary(summary):
        """格式化記帳總結"""
        result = "💰 財務總結\n\n"

        if 'date' in summary:
            result += f"📅 日期: {summary['date'].strftime('%Y-%m-%d')}\n"
        elif 'year' in summary and 'month' in summary:
            result += f"📅 期間: {summary['year']}年{summary['month']}月\n"

        result += f"💸 支出: ${summary['expense']:,.0f}\n"
        result += f"💵 收入: ${summary['income']:,.0f}\n"
        result += f"📊 淨額: ${summary['net']:,.0f}\n"

        if 'categories' in summary and summary['categories']:
            result += "\n📋 支出分類:\n"
            for category, amount in sorted(
                summary['categories'].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                result += f"  • {category}: ${amount:,.0f}\n"

        return result
