from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field

SUPPORTED_INTENTS = {
    "calendar", "expense", "search", "weather",
    "memo", "todo", "translate", "exchange", "chat",
}

# 模組層級單例，避免每次路由都重新建立 OpenAIHelper 實例
_openai_helper = None


def _get_ai_helper():
    global _openai_helper
    if _openai_helper is None:
        from utils.openai_helper import OpenAIHelper
        _openai_helper = OpenAIHelper()
    return _openai_helper


@dataclass
class RoutingResult:
    intent: str
    args: list[str] = field(default_factory=list)
    confidence: float = 0.0


def _rule_route(text: str) -> RoutingResult | None:
    lowered = text.lower().strip()
    if not lowered:
        return RoutingResult(intent="chat", confidence=1.0)

    if any(token in lowered for token in ["天氣", "氣溫", "下雨", "weather"]):
        city = text
        for trigger in ["天氣", "氣溫", "下雨", "weather"]:
            city = city.replace(trigger, "")
        city = city.strip() or "台北"
        return RoutingResult(intent="weather", args=[city], confidence=0.9)

    if any(token in lowered for token in ["搜尋", "查詢", "找", "search"]):
        return RoutingResult(intent="search", confidence=0.8)

    if any(token in lowered for token in ["花", "支出", "收入", "薪水", "記帳", "預算", "元", "塊"]):
        return RoutingResult(intent="expense", confidence=0.8)

    if any(token in lowered for token in ["行程", "會議", "提醒", "明天", "下週", "日程"]):
        return RoutingResult(intent="calendar", confidence=0.8)

    if any(token in lowered for token in ["備忘", "記下", "筆記", "memo"]):
        return RoutingResult(intent="memo", confidence=0.85)

    if any(token in lowered for token in ["待辦", "todo", "任務清單", "要做"]):
        return RoutingResult(intent="todo", confidence=0.85)

    if any(token in lowered for token in ["翻譯", "translate"]):
        return RoutingResult(intent="translate", confidence=0.9)

    if any(token in lowered for token in ["匯率", "換算", "兌換", "美金換", "日幣換", "exchange rate"]):
        return RoutingResult(intent="exchange", confidence=0.9)

    return None


async def _ai_route(text: str) -> RoutingResult | None:
    try:
        ai_helper = _get_ai_helper()
    except Exception:
        return None

    system_prompt = (
        "你是 Telegram 助理的路由器。"
        "請把使用者訊息分類到以下 intent 之一:\n"
        "calendar/expense/search/weather/memo/todo/translate/exchange/chat\n"
        "- translate: 翻譯需求\n"
        "- exchange: 匯率換算\n"
        "回傳 JSON: {\"intent\":\"...\", \"args\":[...], \"confidence\":0~1}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]
    raw = await asyncio.to_thread(ai_helper.chat_completion, messages, 0)
    try:
        data = json.loads(raw)
        intent = data.get("intent", "").strip().lower()
        args = data.get("args", [])
        confidence = float(data.get("confidence", 0.0))
        if intent not in SUPPORTED_INTENTS:
            return None
        if not isinstance(args, list):
            args = []
        return RoutingResult(intent=intent, args=[str(a) for a in args], confidence=confidence)
    except Exception:
        return None


async def route_message(text: str) -> RoutingResult:
    rule_result = _rule_route(text)
    if rule_result and rule_result.confidence >= 0.85:
        return rule_result

    ai_result = await _ai_route(text)
    if ai_result and ai_result.confidence >= 0.55:
        return ai_result

    if rule_result:
        return rule_result
    return RoutingResult(intent="chat", confidence=0.4)
