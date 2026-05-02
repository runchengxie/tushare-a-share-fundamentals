"""Storage utilities for writing dataset outputs and failure reports."""

from __future__ import annotations

import hashlib
import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Iterable, Optional, Sequence

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as _pyarrow_parquet

from .transforms.deduplicate import mark_latest


class _ParquetProxy:
    def read_table(self, *args, **kwargs):
        return _pyarrow_parquet.read_table(*args, **kwargs)

    def write_table(self, *args, **kwargs):
        return _pyarrow_parquet.write_table(*args, **kwargs)

    def __getattr__(self, name: str):
        return getattr(_pyarrow_parquet, name)


pq = _ParquetProxy()

MANIFEST_FILENAME = "_manifest.json"
DATE_BOUND_COLUMNS = ("end_date", "ann_date", "trade_date", "cal_date")


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def merge_and_deduplicate(
    frames: Sequence[pd.DataFrame],
    *,
    group_keys: Sequence[str] | None = None,
) -> Optional[pd.DataFrame]:
    """Combine a list of frames and drop duplicates by ``group_keys``.

    The helper mirrors the previous ``_concat_and_dedup`` implementation but lives
    outside ``MarketDatasetDownloader`` so it can be reused and tested in
    isolation.
    """

    valid = [df for df in frames if df is not None and not df.empty]
    if not valid:
        return None
    prepared: list[pd.DataFrame] = []
    timestamp = pd.Timestamp.utcnow()
    for df in valid:
        frame = df.copy()
        if "retrieved_at" not in frame.columns:
            frame["retrieved_at"] = timestamp
        prepared.append(frame)
    combined = pd.concat(prepared, ignore_index=True)
    for col in ("ts_code", "end_date", "ann_date"):
        if col in combined.columns:
            combined[col] = combined[col].astype(str)
    dedup_keys = [c for c in (group_keys or ()) if c in combined.columns]
    if "retrieved_at" in combined.columns:
        combined["retrieved_at"] = pd.to_datetime(
            combined["retrieved_at"], errors="coerce"
        )
    extra_sort_keys: list[str] = []
    if "retrieved_at" in combined.columns:
        extra_sort_keys.append("retrieved_at")
    if dedup_keys:
        flagged = mark_latest(
            combined,
            group_keys=dedup_keys,
            extra_sort_keys=extra_sort_keys,
        )
        if "is_latest" in flagged.columns:
            combined = flagged[flagged["is_latest"] == 1].drop(columns=["is_latest"])
        else:
            combined = flagged
        combined = combined.drop_duplicates(subset=dedup_keys)
    else:
        combined = combined.drop_duplicates()
    combined = combined.sort_index(ignore_index=True)
    return combined


def _schema_fingerprint(df: pd.DataFrame) -> str:
    schema = [
        {"name": str(column), "dtype": str(df[column].dtype)} for column in df.columns
    ]
    payload = json.dumps(schema, ensure_ascii=True, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _date_bounds(
    df: pd.DataFrame,
    *,
    preferred: str | None = None,
) -> dict[str, str] | None:
    candidates: list[str] = []
    if preferred:
        candidates.append(preferred)
    candidates.extend(DATE_BOUND_COLUMNS)
    for column in candidates:
        if column not in df.columns:
            continue
        values = df[column].dropna().astype(str)
        values = values[~values.str.lower().isin({"", "nan", "nat", "none"})]
        if values.empty:
            continue
        return {
            "column": column,
            "min": str(values.min()),
            "max": str(values.max()),
        }
    return None


def _parquet_files(target_dir: Path) -> list[Path]:
    return sorted(path for path in target_dir.glob("*.parquet") if path.is_file())


def _read_partition_frame(target_dir: Path) -> pd.DataFrame:
    tables = [pq.read_table(path.as_posix()) for path in _parquet_files(target_dir)]
    if not tables:
        return pd.DataFrame()
    return pa.concat_tables(tables).to_pandas()


def write_partition_manifest(
    target_dir: Path,
    *,
    dataset: str,
    partition_key: str,
    frame: pd.DataFrame,
    group_keys: Sequence[str] | None = None,
    preferred_date_col: str | None = None,
) -> None:
    files = [path.name for path in _parquet_files(target_dir)]
    payload: dict[str, object] = {
        "dataset": dataset,
        "partition": partition_key,
        "files": files,
        "row_count": int(len(frame.index)),
        "dedup_keys": [str(key) for key in (group_keys or ())],
        "schema_hash": _schema_fingerprint(frame),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    bounds = _date_bounds(frame, preferred=preferred_date_col)
    if bounds is not None:
        payload["date_bounds"] = bounds
    (target_dir / MANIFEST_FILENAME).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        "utf-8",
    )


def refresh_partition_manifest(
    target_dir: Path,
    *,
    dataset: str,
    partition_key: str,
    group_keys: Sequence[str] | None = None,
    preferred_date_col: str | None = None,
) -> None:
    frame = _read_partition_frame(target_dir)
    write_partition_manifest(
        target_dir,
        dataset=dataset,
        partition_key=partition_key,
        frame=frame,
        group_keys=group_keys,
        preferred_date_col=preferred_date_col,
    )


def _write_parquet_file(frame: pd.DataFrame, path: Path) -> None:
    table = pa.Table.from_pandas(frame, preserve_index=False)
    pq.write_table(table, path.as_posix())


def _write_append_partition(
    partition_new: pd.DataFrame,
    *,
    target_dir: Path,
    dataset: str,
    year: str,
    year_col: str,
    group_keys: Sequence[str] | None = None,
) -> bool:
    deduped = merge_and_deduplicate([partition_new], group_keys=group_keys or ())
    if deduped is None:
        return False
    deduped = deduped.drop(columns=["year"], errors="ignore")
    ensure_dir(target_dir.as_posix())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target_file = target_dir / f"part-{stamp}-{uuid.uuid4().hex[:8]}.parquet"
    tmp_file = target_dir / f".{target_file.name}.tmp"
    _write_parquet_file(deduped, tmp_file)
    shutil.move(tmp_file.as_posix(), target_file.as_posix())
    try:
        refresh_partition_manifest(
            target_dir,
            dataset=dataset,
            partition_key=f"year={year}",
            group_keys=group_keys,
            preferred_date_col=year_col,
        )
    except Exception as exc:  # pragma: no cover - defensive I/O
        print(f"警告：刷新 {target_dir} manifest 失败：{exc}")
    return True


def write_parquet_dataset(  # noqa: C901
    df: pd.DataFrame,
    root: str,
    dataset: str,
    year_col: str,
    *,
    group_keys: Sequence[str] | None = None,
    mode: str = "compact",
) -> bool:
    if df.empty:
        return True
    frame = df.copy()
    frame.columns = [c.lower() for c in frame.columns]
    if year_col not in frame.columns:
        frame[year_col] = None
    frame[year_col] = frame[year_col].astype(str)
    years = frame[year_col].str[:4]
    frame["year"] = years.fillna("unknown").replace(
        to_replace=r"(?i)nan|nat|none", value="unknown", regex=True
    )
    dataset_root = Path(root) / dataset
    ensure_dir(dataset_root.as_posix())
    updated_any = False
    normalized_mode = (mode or "compact").strip().lower()
    if normalized_mode not in {"compact", "append"}:
        raise ValueError(f"未知写入模式：{mode}")
    for year in sorted({y for y in frame["year"].dropna()}):
        partition_new = frame[frame["year"] == year].copy()
        if partition_new.empty:
            continue
        target_dir = dataset_root / f"year={year}"
        if normalized_mode == "append":
            if _write_append_partition(
                partition_new,
                target_dir=target_dir,
                dataset=dataset,
                year=year,
                year_col=year_col,
                group_keys=group_keys,
            ):
                updated_any = True
            continue
        existing = pd.DataFrame()
        if target_dir.exists():
            try:
                existing = _read_partition_frame(target_dir)
            except Exception as exc:  # pragma: no cover - I/O errors
                print(f"警告：读取 {target_dir} 失败：{exc}")
        if not existing.empty:
            existing.columns = [c.lower() for c in existing.columns]
            if "year" not in existing.columns:
                existing["year"] = year
        all_cols = sorted({*partition_new.columns, *existing.columns})
        partition_new = partition_new.reindex(columns=all_cols)
        if not existing.empty:
            existing = existing.reindex(columns=all_cols)
            combined = pd.concat([existing, partition_new], ignore_index=True)
            deduped = merge_and_deduplicate([combined], group_keys=group_keys or ())
            if deduped is None:
                continue
            combined = deduped
        else:
            deduped = merge_and_deduplicate(
                [partition_new], group_keys=group_keys or ()
            )
            if deduped is None:
                continue
            combined = deduped
        combined = combined.drop(columns=["year"], errors="ignore")
        with TemporaryDirectory(dir=dataset_root.as_posix()) as tmpdir:
            tmp_year_dir = Path(tmpdir) / f"year={year}"
            ensure_dir(tmp_year_dir.as_posix())
            _write_parquet_file(combined, tmp_year_dir / "data.parquet")
            write_partition_manifest(
                tmp_year_dir,
                dataset=dataset,
                partition_key=f"year={year}",
                frame=combined,
                group_keys=group_keys,
                preferred_date_col=year_col,
            )
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.move(tmp_year_dir.as_posix(), target_dir.as_posix())
        updated_any = True
    return updated_any


def compact_parquet_partition(
    root: str,
    dataset: str,
    year: str | int,
    *,
    group_keys: Sequence[str] | None = None,
    year_col: str | None = None,
) -> bool:
    dataset_root = Path(root) / dataset
    target_dir = dataset_root / f"year={year}"
    if not target_dir.exists():
        return False
    try:
        existing = _read_partition_frame(target_dir)
    except Exception as exc:  # pragma: no cover - I/O errors
        print(f"警告：读取 {target_dir} 失败：{exc}")
        return False
    if existing.empty:
        return False
    existing.columns = [c.lower() for c in existing.columns]
    combined = merge_and_deduplicate([existing], group_keys=group_keys or ())
    if combined is None:
        return False
    combined = combined.drop(columns=["year"], errors="ignore")
    ensure_dir(dataset_root.as_posix())
    with TemporaryDirectory(dir=dataset_root.as_posix()) as tmpdir:
        tmp_year_dir = Path(tmpdir) / f"year={year}"
        ensure_dir(tmp_year_dir.as_posix())
        _write_parquet_file(combined, tmp_year_dir / "data.parquet")
        write_partition_manifest(
            tmp_year_dir,
            dataset=dataset,
            partition_key=f"year={year}",
            frame=combined,
            group_keys=group_keys,
            preferred_date_col=year_col,
        )
        shutil.rmtree(target_dir)
        shutil.move(tmp_year_dir.as_posix(), target_dir.as_posix())
    return True


def compact_parquet_dataset(
    root: str,
    dataset: str,
    *,
    years: Sequence[str | int] | None = None,
    group_keys: Sequence[str] | None = None,
    year_col: str | None = None,
) -> int:
    dataset_root = Path(root) / dataset
    if years is None:
        years = [
            path.name.split("=", 1)[1]
            for path in sorted(dataset_root.glob("year=*"))
            if path.is_dir()
        ]
    count = 0
    for year in years:
        if compact_parquet_partition(
            root,
            dataset,
            year,
            group_keys=group_keys,
            year_col=year_col,
        ):
            count += 1
    return count


def write_failure_report(
    base_dir: str,
    dataset: str,
    kind: str,
    entries: Iterable[Dict[str, object]],
) -> None:
    failure_root = Path(base_dir) / "_state" / "failures"
    failure_path = failure_root / f"{dataset}_{kind}.json"
    entries = list(entries)
    if not entries:
        if failure_path.exists():
            try:
                failure_path.unlink()
            except OSError:
                pass
        return
    ensure_dir(failure_root.as_posix())
    payload = {
        "dataset": dataset,
        "kind": kind,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "entries": entries,
    }
    failure_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        "utf-8",
    )


__all__ = [
    "ensure_dir",
    "compact_parquet_dataset",
    "compact_parquet_partition",
    "merge_and_deduplicate",
    "pq",
    "refresh_partition_manifest",
    "write_failure_report",
    "write_parquet_dataset",
    "write_partition_manifest",
]
