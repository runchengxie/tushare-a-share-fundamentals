from types import SimpleNamespace

import pandas as pd
import pytest

from tushare_a_fundamentals.commands.compact import cmd_compact

pytestmark = pytest.mark.unit


def test_cmd_compact_dataset_year(tmp_path, capsys):
    partition = tmp_path / "income" / "year=2024"
    partition.mkdir(parents=True)
    pd.DataFrame(
        {
            "ts_code": ["000001.SZ", "000001.SZ"],
            "end_date": ["20241231", "20241231"],
            "retrieved_at": [
                pd.Timestamp("2025-01-01T00:00:00Z"),
                pd.Timestamp("2025-02-01T00:00:00Z"),
            ],
            "value": [1, 2],
        }
    ).to_parquet(partition / "part-a.parquet")

    args = SimpleNamespace(
        dataset_root=str(tmp_path),
        datasets=["income"],
        years="2024",
    )

    cmd_compact(args)

    out = capsys.readouterr().out
    assert "income: 已 compact 1 个分区" in out
    stored = pd.read_parquet(partition / "data.parquet")
    assert len(stored) == 1
    assert stored.loc[0, "value"] == 2
