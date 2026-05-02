"""Quarter and report-period planning helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Optional

PERIOD_NODES = ["0331", "0630", "0930", "1231"]


class Mode:
    ANNUAL = "annual"
    SEMIANNUAL = "semiannual"
    QUARTERLY = "quarterly"


@dataclass
class Plan:
    periodicity: Literal["annual", "semiannual", "quarterly"]


MODE_MAP = {
    Mode.ANNUAL: Plan("annual"),
    Mode.QUARTERLY: Plan("quarterly"),
}


def plan_from_mode(mode: str, periodicity: str | None = None) -> Plan:
    normalized = mode.lower()
    if normalized == "quarter":
        raise ValueError("'quarter' 模式已移除，请改用 'quarterly'")
    try:
        plan = MODE_MAP[normalized]
    except KeyError as exc:
        raise ValueError(f"未知 mode：{mode}") from exc
    return Plan(periodicity or plan.periodicity)


def periods_for_mode_by_years(years: int, mode: str) -> list[str]:
    if years <= 0:
        return []
    cur_year = date.today().year
    nodes = (
        ["1231"]
        if mode == Mode.ANNUAL
        else (["0630", "1231"] if mode == Mode.SEMIANNUAL else PERIOD_NODES)
    )
    out: list[str] = []
    for year in range(cur_year - years + 1, cur_year + 1):
        for node in nodes:
            out.append(f"{year}{node}")
    return out


def periods_by_quarters(quarters: int) -> list[str]:
    if quarters <= 0:
        return []
    year, month = date.today().year, date.today().month
    if month <= 3:
        node = "1231"
        year -= 1
    elif month <= 6:
        node = "0331"
    elif month <= 9:
        node = "0630"
    else:
        node = "0930"
    idx = PERIOD_NODES.index(node)
    result: list[str] = []
    cur_year = year
    cur_idx = idx
    for _ in range(quarters):
        result.append(f"{cur_year}{PERIOD_NODES[cur_idx]}")
        cur_idx -= 1
        if cur_idx < 0:
            cur_idx = len(PERIOD_NODES) - 1
            cur_year -= 1
    return sorted(result)


def backfill_periods(anchor: str, count: int) -> list[str]:
    """Return ``count`` quarterly periods ending at ``anchor``."""

    if count <= 0:
        return []
    if anchor[4:] not in PERIOD_NODES:
        raise ValueError(f"unsupported anchor period: {anchor}")
    year = int(anchor[:4])
    idx = PERIOD_NODES.index(anchor[4:])
    result: list[str] = []
    cur_year = year
    cur_idx = idx
    for _ in range(count):
        result.append(f"{cur_year}{PERIOD_NODES[cur_idx]}")
        cur_idx -= 1
        if cur_idx < 0:
            cur_idx = len(PERIOD_NODES) - 1
            cur_year -= 1
    return sorted(result)


def last_publishable_period(today: date) -> str:
    """Return the last period expected to be publishable at ``today``."""

    year = today.year
    checkpoints = [
        (date(year, 4, 30), f"{year}0331"),
        (date(year, 8, 31), f"{year}0630"),
        (date(year, 10, 31), f"{year}0930"),
        (date(year + 1, 4, 30), f"{year}1231"),
    ]
    last = f"{year - 1}1231"
    for deadline, period in checkpoints:
        if today >= deadline:
            last = period
    return last


def periods_from_range(periods: str, since: str, until: Optional[str]) -> list[str]:
    def to_date(ymd: str) -> date:
        return datetime.strptime(ymd, "%Y-%m-%d").date()

    since_d = to_date(since)
    until_d = to_date(until) if until else date.today()
    if since_d > until_d:
        since_d, until_d = until_d, since_d
    nodes = {
        "annual": ["1231"],
        "semiannual": ["0630", "1231"],
        "quarterly": PERIOD_NODES,
    }[periods]
    result: list[str] = []
    for year in range(since_d.year, until_d.year + 1):
        for node in nodes:
            month_day = f"{node[:2]}-{node[2:]}"
            candidate = date.fromisoformat(f"{year}-{month_day}")
            if since_d <= candidate <= until_d:
                result.append(f"{year}{node}")
    return sorted(result)


def periods_from_cfg(cfg: dict) -> list[str]:
    """Calculate quarter periods from a merged download config."""

    allow_future = bool(cfg.get("allow_future"))
    limit = None if allow_future else last_publishable_period(date.today())

    if cfg.get("since"):
        periods = periods_from_range("quarterly", cfg["since"], cfg.get("until"))
    elif cfg.get("quarters") and cfg["quarters"] > 0:
        quarters = cfg["quarters"]
        periods = (
            periods_by_quarters(quarters)
            if allow_future
            else backfill_periods(limit, quarters)
        )
    else:
        request_years = int(cfg.get("years", 10))
        quarters = request_years * 4
        periods = (
            periods_by_quarters(quarters)
            if allow_future
            else backfill_periods(limit, quarters)
        )
    if not allow_future:
        periods = [period for period in periods if period <= limit]
    return periods


_backfill_periods = backfill_periods
_periods_from_range = periods_from_range
_periods_from_cfg = periods_from_cfg
