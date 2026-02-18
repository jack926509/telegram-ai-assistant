"""時區工具模組：統一使用設定的本地時區"""
from __future__ import annotations

from datetime import datetime

import pytz

import config

_tz: pytz.BaseTzInfo | None = None


def local_tz() -> pytz.BaseTzInfo:
    """回傳設定的本地時區物件（單例）"""
    global _tz
    if _tz is None:
        _tz = pytz.timezone(config.TIMEZONE)
    return _tz


def now_local() -> datetime:
    """回傳本地時間的 naive datetime（供 SQLite 存取用）"""
    return datetime.now(tz=local_tz()).replace(tzinfo=None)
