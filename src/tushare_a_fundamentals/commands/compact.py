from __future__ import annotations

import argparse
from pathlib import Path

from ..config import eprint
from ..dataset_specs import DATASET_SPECS
from ..storage import compact_parquet_dataset


def _parse_years(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    years = [part.strip() for part in raw.split(",") if part.strip()]
    return years or None


def _discover_datasets(root: Path) -> list[str]:
    if not root.exists():
        return []
    return [
        child.name
        for child in sorted(root.iterdir())
        if child.is_dir() and not child.name.startswith("_") and "=" not in child.name
    ]


def cmd_compact(args: argparse.Namespace) -> None:
    root = Path(args.dataset_root or "data")
    datasets = list(args.datasets or [])
    if not datasets:
        datasets = _discover_datasets(root)
    if not datasets:
        eprint(f"错误：未找到可 compact 的数据集目录：{root}")
        raise SystemExit(2)

    years = _parse_years(getattr(args, "years", None))
    total = 0
    for dataset in datasets:
        spec = DATASET_SPECS.get(dataset)
        group_keys = spec.dedup_group_keys or spec.primary_keys if spec else ()
        year_col = spec.default_year_column if spec else None
        count = compact_parquet_dataset(
            root.as_posix(),
            dataset,
            years=years,
            group_keys=group_keys,
            year_col=year_col,
        )
        total += count
        print(f"{dataset}: 已 compact {count} 个分区")
    if total == 0:
        eprint("提示：没有分区被 compact，请检查数据集和年份参数。")
