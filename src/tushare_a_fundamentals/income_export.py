"""Income table transforms and export helpers."""

from __future__ import annotations

import os
import sys
from typing import Optional, Sequence

import pandas as pd

from tushare_a_fundamentals.transforms.deduplicate import (
    mark_latest as _tx_mark_latest,
)
from tushare_a_fundamentals.transforms.deduplicate import (
    select_latest as _tx_select_latest,
)

FLOW_FIELDS = [
    "total_revenue",
    "revenue",
    "total_cogs",
    "operate_profit",
    "total_profit",
    "income_tax",
    "n_income",
    "n_income_attr_p",
    "ebit",
    "ebitda",
    "rd_exp",
]

IDENT_FIELDS = [
    "ts_code",
    "ann_date",
    "f_ann_date",
    "end_date",
    "report_type",
    "comp_type",
    "update_flag",
]

DEFAULT_FIELDS = IDENT_FIELDS + FLOW_FIELDS


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def concat_non_empty(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate DataFrames after dropping empty or all-NA ones."""

    kept: list[pd.DataFrame] = []
    seen_order: list[str] = []
    seen_set: set[str] = set()
    for df in dfs:
        if df is None or not isinstance(df, pd.DataFrame):
            continue
        for col in df.columns:
            if col not in seen_set:
                seen_set.add(col)
                seen_order.append(col)
        df = df.dropna(axis=1, how="all")
        if df.shape[1] == 0 or df.shape[0] == 0:
            continue
        if not df.notna().to_numpy().any():
            continue
        kept.append(df)
    if not kept:
        return pd.DataFrame(columns=seen_order) if seen_order else pd.DataFrame()
    combined = pd.concat(kept, ignore_index=True, copy=False)
    if seen_order:
        combined = combined.loc[
            :, [col for col in seen_order if col in combined.columns]
        ]
    return combined


def select_latest(
    df: pd.DataFrame,
    group_keys: Sequence[str] | None = None,
    extra_sort_keys: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Backward-compatible wrapper around transforms.deduplicate.select_latest."""

    keys = tuple(group_keys or ("ts_code", "end_date"))
    got = _tx_select_latest(df, group_keys=keys, extra_sort_keys=extra_sort_keys)
    if not got.empty:
        keep_cols = list(
            dict.fromkeys(
                [
                    *(
                        DEFAULT_FIELDS
                        if not set(DEFAULT_FIELDS).issubset(got.columns)
                        else got.columns.tolist()
                    )
                ]
            )
        )
        if set(keep_cols).issubset(got.columns):
            got = got[keep_cols]
    return got


def coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def ensure_ts_code(df: pd.DataFrame, *, context: str | None = None) -> pd.DataFrame:
    if "ts_code" in df.columns:
        return df
    if "ticker" in df.columns:
        return df.rename(columns={"ticker": "ts_code"})
    ctx = f"（{context}）" if context else ""
    raise KeyError(f"数据缺少 ts_code 列{ctx}")


def diff_to_single(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    frame = df.copy()
    frame = coerce_numeric(frame, FLOW_FIELDS)
    frame["year"] = frame["end_date"].str.slice(0, 4)
    frame["node"] = frame["end_date"].str.slice(4, 8)
    frame = frame.sort_values(["ts_code", "year", "node"])
    out = frame.copy()
    for col in FLOW_FIELDS:
        if col in frame.columns:
            out[col] = frame.groupby(["ts_code", "year"], as_index=False)[col].diff()
            q1_mask = out["node"] == "0331"
            out.loc[q1_mask, col] = out.loc[q1_mask, col].fillna(
                frame.loc[q1_mask, col]
            )
    return out.drop(columns=["year", "node"])


def single_to_cumulative(single_df: pd.DataFrame) -> pd.DataFrame:
    if single_df.empty:
        return single_df
    frame = single_df.copy()
    frame = coerce_numeric(frame, FLOW_FIELDS)
    frame["year"] = frame["end_date"].str.slice(0, 4)
    frame["node"] = frame["end_date"].str.slice(4, 8)
    frame = frame.sort_values(["ts_code", "year", "node"])
    for col in FLOW_FIELDS:
        if col in frame.columns:
            frame[col] = frame.groupby(["ts_code", "year"], as_index=False)[
                col
            ].cumsum()
    return frame.drop(columns=["year", "node"])


def _ensure_outdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_tables(
    tables: dict[str, pd.DataFrame],
    outdir: str,
    base: str,
    fmt: str,
) -> None:
    _ensure_outdir(outdir)
    reports_dir = os.path.join(outdir, "reports")
    csv_dir = (
        outdir
        if fmt == "csv" and os.path.basename(outdir).lower() == "csv"
        else os.path.join(outdir, "csv")
    )
    parquet_dir = (
        outdir
        if fmt == "parquet" and os.path.basename(outdir).lower() == "parquet"
        else os.path.join(outdir, "parquet")
    )
    _ensure_outdir(reports_dir)
    _ensure_outdir(csv_dir)
    _ensure_outdir(parquet_dir)
    for kind, df in tables.items():
        filename = f"{base}_{kind}.{fmt}"
        path = os.path.join(csv_dir if fmt == "csv" else parquet_dir, filename)
        try:
            if os.path.exists(path):
                print(f"已存在（覆盖）：{path}")
            out_df = df.copy()
            if fmt == "csv":
                out_df.to_csv(path, index=False)
            else:
                out_df.to_parquet(path, index=False)
            print(f"已保存：{path}")
        except Exception as exc:
            eprint(f"错误：保存失败 {path}：{exc}")
            sys.exit(4)


def export_tables(
    tables: dict[str, pd.DataFrame],
    out_dir: str,
    prefix: str,
    fmt: str,
) -> None:
    save_tables({key: df for key, df in tables.items()}, out_dir, prefix, fmt)


def build_datasets_from_raw(
    outdir: str, prefix: str, raw_format: str = "parquet"
) -> bool:
    raw, raw_path = _load_raw_snapshot(outdir, prefix, raw_format)
    if raw is None:
        eprint(f"警告：未找到 {prefix} 的 raw 数据文件，跳过数仓构建")
        return False
    if raw.empty:
        eprint(f"警告：原始数据为空，跳过数仓构建：{raw_path}")
        return False
    raw = ensure_ts_code(raw, context=raw_path)
    inv_dir = os.path.join(outdir, "dataset=inventory_income")
    os.makedirs(inv_dir, exist_ok=True)
    periods = (
        pd.Series(raw["end_date"].astype(str))
        .dropna()
        .drop_duplicates()
        .sort_values()
        .to_frame(name="end_date")
    )
    periods.to_parquet(os.path.join(inv_dir, "periods.parquet"), index=False)
    fact_root = os.path.join(outdir, "dataset=fact_income_cum")
    flagged = _tx_mark_latest(raw, group_keys=("ts_code", "end_date"))
    latest = flagged[flagged["is_latest"] == 1].copy()
    latest["year"] = latest["end_date"].astype(str).str[:4]
    for year, frame in latest.groupby("year"):
        year_dir = os.path.join(fact_root, f"year={year}")
        os.makedirs(year_dir, exist_ok=True)
        frame.drop(columns=["year"]).to_parquet(
            os.path.join(year_dir, "part.parquet"), index=False
        )
    return True


def _load_raw_snapshot(
    outdir: str, prefix: str, raw_format: str = "parquet"
) -> tuple[pd.DataFrame | None, str | None]:
    fmt_preferences: list[str] = []
    if raw_format:
        fmt_preferences.append(raw_format)
    for candidate in ("parquet", "csv"):
        if candidate not in fmt_preferences:
            fmt_preferences.append(candidate)
    for fmt in fmt_preferences:
        fmt_dir = "csv" if fmt == "csv" else "parquet"
        candidate = os.path.join(outdir, fmt_dir, f"{prefix}_vip_quarterly_raw.{fmt}")
        if not os.path.exists(candidate):
            continue
        try:
            if fmt == "csv":
                return pd.read_csv(candidate), candidate
            return pd.read_parquet(candidate), candidate
        except Exception as exc:
            eprint(f"警告：读取 {candidate} 失败：{exc}")
    return None, None


def build_income_export_tables(
    cumulative_df: pd.DataFrame,
    *,
    years: Optional[int],
    kinds: Sequence[str],
    annual_strategy: str,
) -> dict[str, pd.DataFrame]:
    desired = [kind.strip() for kind in kinds if kind and kind.strip()]
    if not desired or cumulative_df is None or cumulative_df.empty:
        return {}

    frame = cumulative_df.copy()
    if "is_latest" in frame.columns:
        frame = frame[frame["is_latest"] == 1]
    if frame.empty:
        return {}

    frame["end_date"] = frame["end_date"].astype(str)
    periods = sorted(frame["end_date"].unique())
    if years is not None:
        requested_quarters = max(int(years) * 4, 0)
        if requested_quarters and len(periods) > requested_quarters:
            keep = set(periods[-requested_quarters:])
            frame = frame[frame["end_date"].isin(keep)]
            periods = sorted(frame["end_date"].unique())
        elif requested_quarters == 0:
            return {}

    built: dict[str, pd.DataFrame] = {}
    if "cumulative" in desired and not frame.empty:
        built["cumulative"] = frame.sort_values(["ts_code", "end_date"]).reset_index(
            drop=True
        )

    single = diff_to_single(frame) if not frame.empty else pd.DataFrame()
    if "single" in desired and not single.empty:
        built["single"] = single.sort_values(["ts_code", "end_date"]).reset_index(
            drop=True
        )

    if "annual" in desired:
        annual = _build_annual(frame, single, annual_strategy)
        if not annual.empty:
            built["annual"] = annual.sort_values(["ts_code", "end_date"]).reset_index(
                drop=True
            )

    return {key: value for key, value in built.items() if not value.empty}


def _build_annual(
    frame: pd.DataFrame, single: pd.DataFrame, annual_strategy: str
) -> pd.DataFrame:
    if annual_strategy == "cumulative":
        return frame[frame["end_date"].str.endswith("1231")].copy()
    if single.empty:
        return pd.DataFrame(columns=["ts_code", "end_date", *FLOW_FIELDS])
    single_frame = single.copy()
    single_frame["year"] = single_frame["end_date"].str[:4]
    aggregations = {col: "sum" for col in FLOW_FIELDS if col in single_frame.columns}
    annual = single_frame.groupby(["ts_code", "year"], as_index=False).agg(aggregations)
    annual["end_date"] = annual["year"].astype(str) + "1231"
    if {"ann_date", "f_ann_date"}.issubset(frame.columns):
        last_ann = (
            frame[frame["end_date"].str.endswith("1231")]
            .sort_values(["ts_code", "f_ann_date", "ann_date"])
            .groupby("ts_code", as_index=False)
            .tail(1)[["ts_code", "ann_date", "f_ann_date"]]
        )
        annual = annual.merge(last_ann, on="ts_code", how="left")
    keep = {"ts_code", "end_date", *FLOW_FIELDS, "ann_date", "f_ann_date"}
    return annual.drop(columns=[col for col in annual.columns if col not in keep])


_concat_non_empty = concat_non_empty
_select_latest = select_latest
_coerce_numeric = coerce_numeric
_diff_to_single = diff_to_single
_single_to_cumulative = single_to_cumulative
_export_tables = export_tables
