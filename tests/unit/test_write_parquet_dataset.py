import json
from pathlib import Path

import pandas as pd
import pytest

import tushare_a_fundamentals.storage as storage
from tushare_a_fundamentals.downloader import write_parquet_dataset
from tushare_a_fundamentals.storage import compact_parquet_partition

pytestmark = pytest.mark.unit


def _read_partition(path: Path) -> pd.DataFrame:
    files = sorted(path.glob("*.parquet"))
    frames = [pd.read_parquet(file) for file in files]
    return pd.concat(frames, ignore_index=True)


def test_write_parquet_dataset_deduplicates(tmp_path):
    df = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ"],
            "ann_date": ["20231231", "20231231"],
            "retrieved_at": [
                pd.Timestamp("2024-01-01T00:00:00Z"),
                pd.Timestamp("2024-02-01T00:00:00Z"),
            ],
            "value": [1, 2],
        }
    )

    ok = write_parquet_dataset(
        df,
        root=tmp_path.as_posix(),
        dataset="dividend",
        year_col="ann_date",
        group_keys=("ts_code", "ann_date"),
    )

    assert ok is True
    partition_dir = tmp_path / "dividend" / "year=2023"
    stored = _read_partition(partition_dir)
    assert len(stored) == 1
    assert stored.loc[0, "value"] == 2

    df_update = pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000002.SZ"],
            "ann_date": ["20231231", "20240131"],
            "retrieved_at": [
                pd.Timestamp("2024-03-01T00:00:00Z"),
                pd.Timestamp("2024-04-01T00:00:00Z"),
            ],
            "value": [3, 4],
        }
    )

    write_parquet_dataset(
        df_update,
        root=tmp_path.as_posix(),
        dataset="dividend",
        year_col="ann_date",
        group_keys=("ts_code", "ann_date"),
    )

    stored_current = _read_partition(partition_dir)
    assert len(stored_current) == 1
    assert stored_current.loc[0, "value"] == 3

    partition_dir_new = tmp_path / "dividend" / "year=2024"
    stored_new = _read_partition(partition_dir_new)
    assert len(stored_new) == 1
    assert stored_new.loc[0, "ts_code"] == "000002.SZ"


def test_write_parquet_dataset_warns_on_read_failure(monkeypatch, tmp_path, capsys):
    target_dir = tmp_path / "dividend" / "year=2023"
    target_dir.mkdir(parents=True)
    (target_dir / "data.parquet").write_bytes(b"")

    def fail_read(path: str) -> object:
        raise OSError("boom")

    monkeypatch.setattr(storage.pq, "read_table", fail_read)

    df = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "ann_date": ["20231231"],
            "retrieved_at": [pd.Timestamp("2024-05-01T00:00:00Z")],
            "value": [1],
        }
    )

    ok = write_parquet_dataset(
        df,
        root=tmp_path.as_posix(),
        dataset="dividend",
        year_col="ann_date",
        group_keys=("ts_code", "ann_date"),
    )

    captured = capsys.readouterr()
    assert ok is True
    assert "警告：读取" in captured.out

    stored = _read_partition(target_dir)
    assert len(stored) == 1
    assert stored.loc[0, "value"] == 1


def test_write_parquet_dataset_writes_manifest(tmp_path):
    df = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "end_date": ["20241231"],
            "retrieved_at": [pd.Timestamp("2025-01-01T00:00:00Z")],
            "value": [1],
        }
    )

    ok = write_parquet_dataset(
        df,
        root=tmp_path.as_posix(),
        dataset="income",
        year_col="end_date",
        group_keys=("ts_code", "end_date"),
    )

    assert ok is True
    manifest_path = tmp_path / "income" / "year=2024" / "_manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    assert manifest["dataset"] == "income"
    assert manifest["partition"] == "year=2024"
    assert manifest["files"] == ["data.parquet"]
    assert manifest["row_count"] == 1
    assert manifest["dedup_keys"] == ["ts_code", "end_date"]
    assert manifest["date_bounds"] == {
        "column": "end_date",
        "min": "20241231",
        "max": "20241231",
    }
    assert len(manifest["schema_hash"]) == 64


def test_append_mode_writes_part_files_and_compacts(tmp_path):
    first = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "end_date": ["20241231"],
            "retrieved_at": [pd.Timestamp("2025-01-01T00:00:00Z")],
            "value": [1],
        }
    )
    second = pd.DataFrame(
        {
            "ts_code": ["000001.SZ"],
            "end_date": ["20241231"],
            "retrieved_at": [pd.Timestamp("2025-02-01T00:00:00Z")],
            "value": [2],
        }
    )

    for frame in (first, second):
        assert write_parquet_dataset(
            frame,
            root=tmp_path.as_posix(),
            dataset="income",
            year_col="end_date",
            group_keys=("ts_code", "end_date"),
            mode="append",
        )

    partition_dir = tmp_path / "income" / "year=2024"
    part_files = sorted(partition_dir.glob("part-*.parquet"))
    assert len(part_files) == 2
    manifest = json.loads((partition_dir / "_manifest.json").read_text("utf-8"))
    assert manifest["files"] == [path.name for path in part_files]
    assert manifest["row_count"] == 2

    ok = compact_parquet_partition(
        tmp_path.as_posix(),
        "income",
        "2024",
        group_keys=("ts_code", "end_date"),
        year_col="end_date",
    )

    assert ok is True
    stored = _read_partition(partition_dir)
    assert len(stored) == 1
    assert stored.loc[0, "value"] == 2
    manifest = json.loads((partition_dir / "_manifest.json").read_text("utf-8"))
    assert manifest["files"] == ["data.parquet"]
    assert manifest["row_count"] == 1
