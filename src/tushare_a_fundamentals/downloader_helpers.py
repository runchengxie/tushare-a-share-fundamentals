"""Small helpers used by the market dataset downloader facade."""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from .dataset_specs import DatasetSpec

DATE_FMT = "%Y%m%d"


@dataclass(frozen=True)
class PeriodCombination:
    report_type: Optional[int] = None
    type_value: Optional[str] = None

    def state_key(self, base: str, spec: DatasetSpec) -> str:
        parts = [base]
        if self.report_type is not None:
            parts.append(f"rt={self.report_type}")
        if spec.type_param and self.type_value is not None:
            parts.append(f"{spec.type_param}={self.type_value}")
        return ":".join(parts)

    def as_params(self, spec: DatasetSpec) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if self.report_type is not None:
            params["report_type"] = self.report_type
        if spec.type_param and self.type_value is not None:
            params[spec.type_param] = self.type_value
        return params

    def describe(self, spec: DatasetSpec) -> str:
        parts: List[str] = []
        if self.report_type is not None:
            parts.append(f"report_type={self.report_type}")
        if spec.type_param and self.type_value is not None:
            parts.append(f"{spec.type_param}={self.type_value}")
        if not parts:
            return "默认组合"
        return ", ".join(parts)


def build_period_combinations(
    report_types: Sequence[int],
    type_values: Sequence[str],
) -> list[PeriodCombination]:
    rt_values = list(report_types) if report_types else [None]
    type_opts = list(type_values) if type_values else [None]
    return [
        PeriodCombination(report_type=rt, type_value=tv)
        for rt in rt_values
        for tv in type_opts
    ]


def resolve_report_types(spec: DatasetSpec, options: dict[str, Any]) -> list[int]:
    if "report_types" in options:
        vals = options["report_types"]
        if isinstance(vals, str):
            parts = [part.strip() for part in vals.split(",") if part.strip()]
            return [int(part) for part in parts]
        if isinstance(vals, Sequence):
            return [int(value) for value in vals]
    if spec.report_types:
        return list(spec.report_types)
    return []


def resolve_type_values(spec: DatasetSpec, options: dict[str, Any]) -> list[str]:
    if spec.type_param is None:
        return []
    if spec.type_param in options:
        vals = options[spec.type_param]
        if isinstance(vals, str):
            return [part.strip() for part in vals.split(",") if part.strip()]
        if isinstance(vals, Sequence):
            return [str(value) for value in vals]
    if spec.type_values:
        return list(spec.type_values)
    return []


def normalize_code_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        candidates = raw.replace("\n", ",").split(",")
        items = [candidate.strip() for candidate in candidates if candidate.strip()]
    elif isinstance(raw, Sequence) and not isinstance(raw, (bytes, bytearray)):
        items = [str(candidate).strip() for candidate in raw if str(candidate).strip()]
    else:
        items = [str(raw).strip()]
    seen: set[str] = set()
    unique: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def normalize_period(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if len(text) == 10 and text[4] == "-" and text[7] == "-":
        text = text.replace("-", "")
    if len(text) != 8:
        return None
    return text


def max_period(value: Optional[str], floor: Optional[str]) -> Optional[str]:
    if value is None:
        return floor
    if floor is None:
        return value
    return max(value, floor)


def list_date_to_period(raw: Any, quarter_end_for) -> Optional[str]:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    normalized = normalize_period(text)
    if normalized is None:
        return None
    try:
        day = datetime.strptime(normalized, DATE_FMT).date()
    except ValueError:
        return None
    return quarter_end_for(day).strftime(DATE_FMT)


def summarize_params(params: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key, value in sorted(params.items()):
        if "token" in key.lower():
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            summary[key] = value
        elif isinstance(value, (list, tuple, set)):
            summary[key] = ",".join(sorted(str(item) for item in value))
        else:
            summary[key] = str(value)
    return summary


def expected_fields(fields: str) -> set[str]:
    items = [part.strip() for part in re.split(r"[\n,]", fields) if part.strip()]
    return set(items)


def extract_truncation_metadata(
    df: Optional[pd.DataFrame],
    *,
    period: Optional[str] = None,
    ts_code: Optional[str] = None,
    window: Optional[str] = None,
) -> Optional[dict[str, Any]]:
    if df is None or not hasattr(df, "attrs"):
        return None
    if not df.attrs.get("page_limit_hit"):
        return None
    metadata: dict[str, Any] = {"page_limit_hit": True}
    if period is not None:
        metadata["period"] = period
    if ts_code is not None:
        metadata["ts_code"] = ts_code
    if window is not None:
        metadata["window"] = window
    pagination = df.attrs.get("pagination_info")
    if isinstance(pagination, dict):
        metadata["pagination"] = pagination
    else:
        metadata.setdefault("pagination", {})
    return metadata
