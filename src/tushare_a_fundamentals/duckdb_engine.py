from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable, Sequence


class DuckDBUnavailableError(RuntimeError):
    pass


class DatasetNotFoundError(RuntimeError):
    def __init__(self, dataset: str) -> None:
        super().__init__(dataset)
        self.dataset = dataset


def require_duckdb():
    try:
        import duckdb  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover - depends on optional package
        raise DuckDBUnavailableError(
            "缺少可选依赖 duckdb。请安装：uv pip install 'duckdb>=0.10.0'，"
            "或使用默认 pandas 引擎。"
        ) from exc
    return duckdb


def connect():
    duckdb = require_duckdb()
    return duckdb.connect(database=":memory:")


def quote_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _list_literal(values: Sequence[str]) -> str:
    return "[" + ", ".join(_quote_literal(value) for value in values) + "]"


def parquet_files(source: Path, *, years: Iterable[str] | None = None) -> list[Path]:
    if years is None:
        return sorted(path for path in source.rglob("*.parquet") if path.is_file())
    files: list[Path] = []
    for year in years:
        partition = source / f"year={year}"
        files.extend(path for path in partition.glob("*.parquet") if path.is_file())
    return sorted(files)


def read_parquet_sql(source: Path, *, years: Iterable[str] | None = None) -> str:
    files = [source] if source.is_file() else parquet_files(source, years=years)
    if not files:
        raise FileNotFoundError(source)
    paths = [path.as_posix() for path in files]
    return (
        "read_parquet("
        f"{_list_literal(paths)}, "
        "hive_partitioning=true, union_by_name=true"
        ")"
    )


def register_dataset_view(
    conn,
    dataset_root: Path,
    dataset: str,
    *,
    years: Iterable[str] | None = None,
) -> None:
    source = dataset_root / dataset
    if not source.exists():
        raise DatasetNotFoundError(dataset)
    relation = read_parquet_sql(source, years=years)
    view_name = quote_identifier(dataset)
    conn.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM {relation}")


def discover_datasets(dataset_root: Path) -> list[str]:
    if not dataset_root.exists():
        return []
    return [
        child.name
        for child in sorted(dataset_root.iterdir())
        if child.is_dir() and not child.name.startswith("_") and "=" not in child.name
    ]


def register_all_dataset_views(
    conn,
    dataset_root: Path,
    *,
    years: Iterable[str] | None = None,
) -> list[str]:
    registered: list[str] = []
    for dataset in discover_datasets(dataset_root):
        try:
            register_dataset_view(conn, dataset_root, dataset, years=years)
        except FileNotFoundError:
            continue
        registered.append(dataset)
    return registered


_MISSING_TABLE_RE = re.compile(r"Table with name ([A-Za-z_][A-Za-z0-9_]*) does not")


def missing_dataset_from_error(message: str, dataset_root: Path) -> str | None:
    match = _MISSING_TABLE_RE.search(message)
    if not match:
        return None
    dataset = match.group(1)
    if (dataset_root / dataset).exists():
        return None
    return dataset
