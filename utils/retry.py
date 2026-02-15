from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable

import aiohttp

RETRYABLE_HTTP_STATUS = {429, 500, 502, 503, 504}


def is_retryable_http_error(error: Exception) -> bool:
    """判斷是否為可重試的 HTTP/網路錯誤"""
    if isinstance(error, aiohttp.ClientResponseError):
        return error.status in RETRYABLE_HTTP_STATUS

    return isinstance(
        error,
        (
            aiohttp.ClientConnectionError,
            aiohttp.ServerTimeoutError,
            aiohttp.ClientOSError,
            aiohttp.ClientPayloadError,
            asyncio.TimeoutError,
        ),
    )


async def retry_async(
    operation: Callable[[], Awaitable[Any]],
    *,
    attempts: int = 3,
    base_delay: float = 0.6,
    max_delay: float = 4.0,
    should_retry: Callable[[Exception], bool] | None = None,
) -> Any:
    """非同步重試封裝 (指數退避)"""
    last_error: Exception | None = None

    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except Exception as error:  # noqa: PERF203
            last_error = error
            retry_allowed = should_retry(error) if should_retry else True
            if attempt >= attempts or not retry_allowed:
                raise

            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            await asyncio.sleep(delay)

    if last_error:
        raise last_error

    raise RuntimeError("retry_async 發生未預期狀況")


async def run_in_thread_with_retry(
    func: Callable[..., Any],
    *args: Any,
    attempts: int = 3,
    base_delay: float = 0.6,
    max_delay: float = 4.0,
    should_retry: Callable[[Exception], bool] | None = None,
    **kwargs: Any,
) -> Any:
    """同步函式包裝為 thread 執行並附帶重試"""

    async def _operation() -> Any:
        return await asyncio.to_thread(func, *args, **kwargs)

    return await retry_async(
        _operation,
        attempts=attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        should_retry=should_retry,
    )
