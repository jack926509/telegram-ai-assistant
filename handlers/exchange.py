"""匯率查詢 handler — 使用 frankfurter.app 免費 API（無需 API Key）"""
import asyncio
import logging
import re

import aiohttp
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

_API_BASE = "https://api.frankfurter.app"
_DEFAULT_TIMEOUT = aiohttp.ClientTimeout(total=10)

# 常用貨幣中文別名
_CURRENCY_ALIAS = {
    '美金': 'USD', '美元': 'USD', 'usd': 'USD',
    '台幣': 'TWD', '新台幣': 'TWD', 'twd': 'TWD',
    '港幣': 'HKD', 'hkd': 'HKD',
    '日圓': 'JPY', '日幣': 'JPY', 'jpy': 'JPY',
    '韓元': 'KRW', 'krw': 'KRW',
    '人民幣': 'CNY', '人民币': 'CNY', 'cny': 'CNY',
    '歐元': 'EUR', 'eur': 'EUR',
    '英鎊': 'GBP', 'gbp': 'GBP',
    '澳幣': 'AUD', '澳元': 'AUD', 'aud': 'AUD',
    '加拿大元': 'CAD', 'cad': 'CAD',
    '新加坡元': 'SGD', 'sgd': 'SGD',
}

# 自然語言 pattern: [金額] [來源幣] 換 [目標幣]
_NATURAL_RE = re.compile(
    r'(\d+(?:\.\d+)?)\s*([^\s換兌]+)\s*(?:換|兌|to|into)\s*([^\s？?]+)',
    re.IGNORECASE
)


def _resolve_currency(raw: str) -> str:
    """解析貨幣別名或直接返回大寫 ISO 代碼"""
    return _CURRENCY_ALIAS.get(raw.lower(), raw.upper())


async def _fetch_rate(amount: float, from_cur: str, to_cur: str) -> dict | None:
    """從 frankfurter.app 取得匯率"""
    url = f"{_API_BASE}/latest"
    params = {"from": from_cur, "to": to_cur, "amount": amount}
    try:
        async with aiohttp.ClientSession(timeout=_DEFAULT_TIMEOUT) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    return None
                return await resp.json()
    except Exception:
        logger.exception("fetch_rate failed: %s→%s", from_cur, to_cur)
        return None


async def exchange_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/exchange [金額] [來源幣] [目標幣(可省略)] — 即時匯率換算

    例:
      /exchange 100 USD TWD    → 100 美金換台幣
      /exchange 100 USD        → 100 美金換台幣（預設目標）
      /exchange 1 EUR          → 1 歐元換台幣
    """
    user_id = update.effective_user.id

    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "💱 用法: /exchange [金額] [來源幣] [目標幣]\n\n"
            "例:\n"
            "• /exchange 100 USD TWD\n"
            "• /exchange 100 USD        （預設換台幣）\n"
            "• /exchange 1 EUR JPY\n\n"
            "支援: USD 美金 / TWD 台幣 / JPY 日圓 / EUR 歐元 / GBP 英鎊 / HKD 港幣 / CNY 人民幣 等"
        )
        return

    try:
        amount = float(context.args[0])
    except ValueError:
        await update.message.reply_text("請輸入有效的金額數字，例如: /exchange 100 USD TWD")
        return

    from_cur = _resolve_currency(context.args[1])
    to_cur = _resolve_currency(context.args[2]) if len(context.args) >= 3 else 'TWD'

    if from_cur == to_cur:
        await update.message.reply_text("來源幣與目標幣相同！")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    data = await _fetch_rate(amount, from_cur, to_cur)
    if not data or to_cur not in data.get('rates', {}):
        await update.message.reply_text(
            f"無法查詢 {from_cur} → {to_cur} 匯率，請確認貨幣代碼是否正確。"
        )
        return

    result = data['rates'][to_cur]
    rate = result / amount
    date = data.get('date', '')
    await update.message.reply_text(
        f"💱 匯率換算\n\n"
        f"{amount:,.2f} {from_cur}  =  {result:,.2f} {to_cur}\n\n"
        f"匯率: 1 {from_cur} = {rate:.4f} {to_cur}\n"
        f"📅 資料日期: {date}"
    )


async def natural_exchange_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """自然語言觸發匯率查詢（由 intent_router 路由）

    支援格式: 100美金換台幣 / 1000元日幣兌換台幣
    """
    user_id = update.effective_user.id
    text = update.message.text

    match = _NATURAL_RE.search(text)
    if not match:
        await update.message.reply_text(
            "請輸入格式如「100美金換台幣」或使用 /exchange 100 USD TWD"
        )
        return

    amount = float(match.group(1))
    from_cur = _resolve_currency(match.group(2))
    to_cur = _resolve_currency(match.group(3))

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    data = await _fetch_rate(amount, from_cur, to_cur)
    if not data or to_cur not in data.get('rates', {}):
        await update.message.reply_text(
            f"無法查詢 {from_cur} → {to_cur} 匯率，請確認貨幣名稱是否正確。"
        )
        return

    result = data['rates'][to_cur]
    rate = result / amount
    date = data.get('date', '')
    await update.message.reply_text(
        f"💱 匯率換算\n\n"
        f"{amount:,.2f} {from_cur}  =  {result:,.2f} {to_cur}\n\n"
        f"匯率: 1 {from_cur} = {rate:.4f} {to_cur}\n"
        f"📅 資料日期: {date}"
    )
