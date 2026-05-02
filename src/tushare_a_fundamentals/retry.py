"""Retry policy utilities for TuShare API calls."""

from __future__ import annotations

import random
import sys
import time
from dataclasses import dataclass
from typing import Callable, Optional, Tuple, TypeVar

T = TypeVar("T")

_FATAL_EXCEPTION_TYPES: Tuple[type, ...] = (
    AttributeError,
    ValueError,
    TypeError,
)

_FATAL_MESSAGE_KEYWORDS: Tuple[str, ...] = (
    "permission",
    "权限",
    "无权限",
    "token",
    "denied",
    "unauthorized",
    "未授权",
    "认证失败",
    "参数错误",
    "parameter error",
    "invalid parameter",
    "invalid token",
    "missing token",
    "missing parameter",
)


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


class RetryExhaustedError(RuntimeError):
    """Raised when a retryable operation keeps failing beyond the limit."""

    def __init__(self, description: str, last_exception: Exception) -> None:
        super().__init__(description)
        self.last_exception = last_exception


@dataclass
class RetryPolicy:
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    jitter: float = 0.2

    def __post_init__(self) -> None:
        if self.max_retries < 0:
            self.max_retries = 0
        if self.base_delay <= 0:
            self.base_delay = 0.1
        if self.max_delay < self.base_delay:
            self.max_delay = self.base_delay
        if self.jitter < 0:
            self.jitter = 0.0

    def is_retryable(self, exc: Exception) -> bool:
        if isinstance(exc, _FATAL_EXCEPTION_TYPES):
            return False
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code is not None:
            try:
                code = int(status_code)
            except (TypeError, ValueError):
                code = None
            if code is not None:
                if code >= 500 or code == 429:
                    return True
                if 400 <= code < 500:
                    return False
        message = str(exc)
        if not message:
            return True
        lowered = message.lower()
        for keyword in _FATAL_MESSAGE_KEYWORDS:
            if keyword in lowered:
                return False
        return True

    def next_delay(self, retry_index: int) -> float:
        base = min(self.base_delay * (2**retry_index), self.max_delay)
        if self.jitter <= 0:
            return base
        low = base * max(0.0, 1 - self.jitter)
        high = base * (1 + self.jitter)
        if low == high:
            return low
        return random.uniform(low, high)


def call_with_retry(
    func: Callable[[], T],
    *,
    policy: Optional[RetryPolicy] = None,
    description: Optional[str] = None,
    on_retry: Optional[Callable[[int, Exception, float], None]] = None,
    sleep_func: Callable[[float], None] = time.sleep,
) -> T:
    """Execute ``func`` with retry and exponential backoff."""

    used_policy = policy or RetryPolicy()
    retries = 0
    while True:
        try:
            return func()
        except Exception as exc:
            if not used_policy.is_retryable(exc):
                raise
            if retries >= used_policy.max_retries:
                raise RetryExhaustedError(description or str(exc), exc) from exc
            wait_seconds = used_policy.next_delay(retries)
            retries += 1
            if on_retry is not None:
                on_retry(retries, exc, wait_seconds)
            else:
                label = description or "调用"
                eprint(
                    "警告："
                    f"{label} 异常，{wait_seconds:.1f}s 后重试"
                    f"（第 {retries}/{used_policy.max_retries} 次）：{exc}"
                )
            sleep_func(wait_seconds)
