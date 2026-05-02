"""TuShare client, token pool, and credit checking helpers."""

from __future__ import annotations

import math
import os
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from heapq import heappop, heappush
from itertools import count
from typing import Any, Deque, Optional, Sequence, Tuple

import pandas as pd

_GLOBAL_TOKEN: Optional[str] = None


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


class _TokenClient:
    """Internal helper for ``ProPool`` representing a single TuShare token."""

    def __init__(self, token: str, rate: int) -> None:
        import tushare as ts

        self.token = token
        self.max_per_minute = max(0, int(rate))
        self.calls: Deque[float] = deque()
        self._lock = threading.Lock()
        self.pro = ts.pro_api(token=token)

    def try_acquire(self, now: float) -> Tuple[bool, float]:
        with self._lock:
            window_start = now - 60.0
            while self.calls and self.calls[0] < window_start:
                self.calls.popleft()
            if self.max_per_minute <= 0:
                return True, 0.0
            if len(self.calls) < self.max_per_minute:
                self.calls.append(now)
                return True, 0.0
            if not self.calls:
                return False, 0.05
            wait_for = self.calls[0] + 60.0 - now
            return False, max(wait_for, 0.0)

    def set_rate(self, rate: int) -> None:
        with self._lock:
            self.max_per_minute = max(0, int(rate))
            if self.max_per_minute == 0:
                self.calls.clear()


class ProPool:
    """Round-robin wrapper that balances API calls across multiple tokens."""

    __is_token_pool__ = True

    def __init__(self, tokens: Sequence[str], per_token_rate: int = 90) -> None:
        filtered: list[str] = []
        for token in tokens:
            if token and token not in filtered:
                filtered.append(token)
        if not filtered:
            raise ValueError("ProPool requires at least one token")
        self._clients = [_TokenClient(token, per_token_rate) for token in filtered]
        self._lock = threading.Lock()
        self._sequence = count()
        self._availability: list[tuple[float, int, _TokenClient]] = []
        for client in self._clients:
            heappush(self._availability, (0.0, next(self._sequence), client))
        self._rate = max(0, int(per_token_rate))

    def set_rate(self, rate: Optional[int]) -> None:
        value = 0 if rate is None else max(0, int(rate))
        self._rate = value
        for client in self._clients:
            client.set_rate(value)
        with self._lock:
            self._availability.clear()
            for client in self._clients:
                heappush(self._availability, (0.0, next(self._sequence), client))

    def _acquire_client(self) -> _TokenClient:
        while True:
            attempt_time = time.time()
            sleep_for = 0.05
            with self._lock:
                next_ready, _, client = heappop(self._availability)
                if next_ready > attempt_time:
                    sleep_for = next_ready - attempt_time
                    heappush(
                        self._availability,
                        (next_ready, next(self._sequence), client),
                    )
                    client = None
            if client is None:
                time.sleep(max(sleep_for, 0.05))
                continue
            now = time.time()
            acquired, wait = client.try_acquire(now)
            next_available = now if wait <= 0 else now + wait
            with self._lock:
                heappush(
                    self._availability,
                    (next_available, next(self._sequence), client),
                )
            if acquired:
                return client

    def query(self, *args: Any, **kwargs: Any):
        client = self._acquire_client()
        return client.pro.query(*args, **kwargs)

    def __getattr__(self, name: str):
        sample = getattr(self._clients[0].pro, name, None)
        if callable(sample):

            def _caller(*args: Any, **kwargs: Any):
                client = self._acquire_client()
                target = getattr(client.pro, name)
                return target(*args, **kwargs)

            return _caller
        if sample is not None:
            return sample

        def _fallback(*args: Any, **kwargs: Any):
            client = self._acquire_client()
            return client.pro.query(name, *args, **kwargs)

        return _fallback


@dataclass
class ProContext:
    any_client: Any
    vip_client: Any | None
    tokens: list[str]
    vip_tokens: list[str]

    def vip_or_default(self) -> Any:
        return self.vip_client or self.any_client


@dataclass
class TokenInfo:
    token: str
    credits: Optional[float]
    is_vip: bool
    source: Optional[str] = None
    detection_failed: bool = False


def _mask_token(token: str) -> str:
    trimmed = (token or "").strip()
    if len(trimmed) <= 8:
        return trimmed[:2] + "***" if trimmed else "<empty>"
    return f"{trimmed[:4]}...{trimmed[-4:]}"


def _split_token_list(raw: Optional[str]) -> list[str]:
    if not raw:
        return []
    items = [item.strip() for item in raw.split(",")]
    return [item for item in items if item]


def _env_flag(name: str, default: bool = True) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    lowered = raw.strip().lower()
    return lowered not in {"0", "false", "no", "off"}


def _format_credit_value(value: Optional[float]) -> str:
    if value is None:
        return "未知"
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError):
        try:
            num = float(value)
        except (TypeError, ValueError):
            return str(value)
        if math.isclose(num, round(num)):
            return f"{int(round(num))}"
        return f"{num:.2f}"
    if dec == dec.to_integral():
        return f"{int(dec)}"
    return str(dec.normalize())


def _evaluate_token_info(
    token: str, manual_vip: Sequence[str], detect_vip: bool
) -> TokenInfo:
    credits: Optional[float] = None
    is_vip = False
    source: Optional[str] = None
    detection_failed = False
    if token in manual_vip:
        is_vip = True
        source = "手动指定"
        if detect_vip:
            credits = _probe_token_credits(token)
            detection_failed = credits is None
    elif detect_vip:
        credits = _probe_token_credits(token)
        detection_failed = credits is None
        if _credits_meet_requirement(credits, 5000):
            is_vip = True
            source = "自动识别"
    return TokenInfo(
        token=token,
        credits=credits,
        is_vip=is_vip,
        source=source,
        detection_failed=detection_failed,
    )


def _format_token_log(
    index: int,
    info: TokenInfo,
    manual_vip: Sequence[str],
    detect_vip: bool,
) -> str:
    label = "VIP" if info.is_vip else "普通"
    credit_text = _format_credit_value(info.credits)
    notes: list[str] = []
    if info.source:
        notes.append(f"来源：{info.source}")
    if detect_vip and info.detection_failed:
        notes.append("积分检测失败")
    elif not detect_vip and info.token not in manual_vip:
        notes.append("未启用自动检测")
    message = (
        f"  - token#{index} {_mask_token(info.token)}：{label}（积分：{credit_text}）"
    )
    if notes:
        message += "，" + "，".join(notes)
    return message


def _derive_vip_tokens(
    tokens: Sequence[str],
    infos: Sequence[TokenInfo],
    manual_vip: Sequence[str],
    detect_vip: bool,
) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    if manual_vip:
        vip_tokens = [token for token in tokens if token in manual_vip]
        missing = [token for token in manual_vip if token not in tokens]
        if missing:
            masked = ", ".join(_mask_token(token) for token in missing)
            warnings.append(
                f"警告：TUSHARE_VIP_TOKENS 包含未参与轮询的 token：{masked}"
            )
        return vip_tokens, warnings
    if detect_vip:
        vip_tokens = [info.token for info in infos if info.is_vip]
        return vip_tokens, warnings
    warnings.append(
        "警告：未启用自动检测且未指定 TUSHARE_VIP_TOKENS，"
        "已默认第一个 token 作为 VIP，请确认其积分 ≥5000。"
    )
    return list(tokens[:1]), warnings


def init_pro_api(token: Optional[str]) -> ProContext:
    global _GLOBAL_TOKEN

    token_env = os.getenv("TUSHARE_TOKEN")
    primary = token or token_env
    if not primary:
        eprint(
            "错误：缺少 TuShare token。请通过环境变量 TUSHARE_TOKEN 或 --token 提供。"
        )
        sys.exit(2)

    tokens: list[str] = []
    for candidate in (primary, os.getenv("TUSHARE_TOKEN_2")):
        if candidate and candidate not in tokens:
            tokens.append(candidate)

    manual_vip = _split_token_list(os.getenv("TUSHARE_VIP_TOKENS"))
    detect_vip = _env_flag("TUSHARE_DETECT_VIP", default=True)

    if len(tokens) > 1:
        print("提示：检测到多个 TuShare token，将自动分配 VIP 凭证。")
    if manual_vip:
        print("提示：已根据环境变量 TUSHARE_VIP_TOKENS 指定 VIP token。")
    elif not detect_vip and len(tokens) > 1:
        print("提示：已禁用自动检测 VIP token（TUSHARE_DETECT_VIP=false）。")

    token_infos = [
        _evaluate_token_info(token_value, manual_vip, detect_vip)
        for token_value in tokens
    ]
    for idx, info in enumerate(token_infos, start=1):
        print(_format_token_log(idx, info, manual_vip, detect_vip))

    vip_tokens, derived_warnings = _derive_vip_tokens(
        tokens, token_infos, manual_vip, detect_vip
    )
    for warning in derived_warnings:
        print(warning)

    if not vip_tokens and detect_vip:
        print(
            "警告：未检测到满足 VIP 门槛的 token，use_vip=true 时将无法批量抓取，"
            "请确认至少一个 token 拥有 ≥5000 积分或设置 TUSHARE_VIP_TOKENS。"
        )

    try:
        import tushare as ts

        if len(tokens) > 1:
            any_client: Any = ProPool(tokens, per_token_rate=90)
        else:
            ts.set_token(tokens[0])
            any_client = ts.pro_api()

        vip_client: Any | None = None
        if vip_tokens:
            if len(vip_tokens) == len(tokens):
                vip_client = any_client
            elif len(vip_tokens) == 1:
                vip_client = ts.pro_api(token=vip_tokens[0])
            else:
                vip_client = ProPool(vip_tokens, per_token_rate=90)
    except Exception as exc:
        eprint(f"错误：初始化 TuShare 失败：{exc}")
        sys.exit(2)

    _GLOBAL_TOKEN = vip_tokens[0] if vip_tokens else tokens[0]
    return ProContext(
        any_client=any_client,
        vip_client=vip_client,
        tokens=tokens,
        vip_tokens=vip_tokens,
    )


def _sum_credits_from_df(df: pd.DataFrame | None) -> Optional[float]:
    if df is None or not hasattr(df, "empty") or df.empty:
        return None
    cols = list(df.columns)
    if "到期积分" in cols:
        target_cols = ["到期积分"]
    else:
        target_cols = [
            col for col in cols if ("积分" in str(col)) or ("point" in str(col).lower())
        ]
    if not target_cols:
        return None
    total = 0.0
    for col in target_cols:
        try:
            series = pd.to_numeric(
                df[col].astype(str).str.replace(",", ""), errors="coerce"
            )
        except Exception:
            continue
        if series.notna().any():
            try:
                total += float(series.sum(skipna=True))
            except Exception:
                continue
    return total if total > 0 else None


def _available_credits(pro, *, token: str | None = None) -> float | None:
    attempts: list[Any] = []
    if token:
        attempts.append(lambda: pro.user(token=token))
    attempts.append(pro.user)

    if token is None:
        token_candidate = (
            _GLOBAL_TOKEN or os.getenv("TUSHARE_TOKEN") or os.getenv("TUSHARE_API_KEY")
        )
        if token_candidate:

            def _fallback() -> Any:
                import tushare as ts

                proxy = ts.pro_api(token=token_candidate)
                return proxy.user(token=token_candidate)

            attempts.append(_fallback)

    for attempt in attempts:
        try:
            df = attempt()
        except Exception:
            continue
        total = _sum_credits_from_df(df)
        if total is not None:
            return total
    return None


def _credits_meet_requirement(value: Any, required: int = 5000) -> bool:
    if value is None:
        return False
    try:
        total_d = Decimal(str(value))
        required_d = Decimal(str(required))
    except (InvalidOperation, ValueError):
        try:
            total_f = float(value)
            required_f = float(required)
        except (TypeError, ValueError):
            return False
        if total_f >= required_f:
            return True
        return math.isclose(total_f, required_f, rel_tol=1e-6, abs_tol=1e-3)

    if total_d >= required_d:
        return True
    return 0 <= (required_d - total_d) <= Decimal("0.001")


def _has_enough_credits(pro, required: int = 5000) -> bool:
    total = _available_credits(pro)
    return _credits_meet_requirement(total, required)


def _probe_token_credits(token: str) -> Optional[float]:
    try:
        import tushare as ts

        client = ts.pro_api(token=token)
    except Exception:
        return None
    return _available_credits(client, token=token)


def ensure_enough_credits(pro, required: int = 5000) -> None:
    """Exit with an error message when available credits are insufficient."""

    if _has_enough_credits(pro, required=required):
        return
    total = _available_credits(pro)
    detected = "0" if total is None else repr(total)
    eprint(f"错误：全市场批量需要至少 {required} 积分。（检测到总积分：{detected}）")
    sys.exit(2)
