from __future__ import annotations

import argparse
from pathlib import Path

from ..config import eprint
from ..duckdb_engine import (
    DuckDBUnavailableError,
    connect,
    missing_dataset_from_error,
    register_all_dataset_views,
)


def _parse_years(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    years = [part.strip() for part in raw.split(",") if part.strip()]
    return years or None


def cmd_query(args: argparse.Namespace) -> None:
    dataset_root = Path(args.dataset_root or "data")
    years = _parse_years(getattr(args, "year", None))
    try:
        conn = connect()
    except DuckDBUnavailableError as exc:
        eprint(f"错误：{exc}")
        raise SystemExit(2) from exc

    try:
        registered = register_all_dataset_views(conn, dataset_root, years=years)
        if not registered:
            eprint(f"错误：未找到可查询的数据集目录：{dataset_root}")
            raise SystemExit(2)
        try:
            result = conn.execute(args.sql)
        except Exception as exc:
            missing = missing_dataset_from_error(str(exc), dataset_root)
            if missing:
                eprint(f"错误：未找到数据集：{missing}")
                raise SystemExit(2) from exc
            raise
        out = getattr(args, "out", None)
        if out:
            out_path = Path(out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            if args.out_format == "parquet":
                result.fetchdf().to_parquet(out_path, index=False)
            else:
                result.fetchdf().to_csv(out_path, index=False)
            print(f"已保存：{out_path}")
            return
        df = result.fetchdf()
        if df.empty:
            print("查询结果为空")
        else:
            print(df.to_string(index=False))
    finally:
        conn.close()
