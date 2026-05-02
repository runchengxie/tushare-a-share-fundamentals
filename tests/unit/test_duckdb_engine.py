import importlib.util
from types import SimpleNamespace

import pandas as pd
import pytest

from tushare_a_fundamentals import duckdb_engine as engine
from tushare_a_fundamentals.commands import query as query_cmd

pytestmark = pytest.mark.unit


def test_read_parquet_sql_filters_year(tmp_path):
    source = tmp_path / "income"
    (source / "year=2023").mkdir(parents=True)
    (source / "year=2024").mkdir(parents=True)
    pd.DataFrame({"x": [1]}).to_parquet(source / "year=2023" / "data.parquet")
    pd.DataFrame({"x": [2]}).to_parquet(source / "year=2024" / "data.parquet")

    sql = engine.read_parquet_sql(source, years=["2024"])

    assert "year=2024/data.parquet" in sql
    assert "year=2023/data.parquet" not in sql
    assert "union_by_name=true" in sql


def test_query_missing_duckdb(monkeypatch, capsys):
    def fail_connect():
        raise engine.DuckDBUnavailableError("missing duckdb")

    monkeypatch.setattr(query_cmd, "connect", fail_connect)
    args = SimpleNamespace(
        dataset_root="data",
        year=None,
        sql="select 1",
        out=None,
        out_format="csv",
    )

    with pytest.raises(SystemExit) as excinfo:
        query_cmd.cmd_query(args)

    captured = capsys.readouterr()
    assert excinfo.value.code == 2
    assert "错误：missing duckdb" in captured.err


@pytest.mark.skipif(
    importlib.util.find_spec("duckdb") is None,
    reason="duckdb optional dependency is not installed",
)
def test_query_outputs_result(tmp_path, capsys):
    dataset = tmp_path / "income" / "year=2024"
    dataset.mkdir(parents=True)
    pd.DataFrame({"ts_code": ["000001.SZ"], "value": [1]}).to_parquet(
        dataset / "data.parquet"
    )
    args = SimpleNamespace(
        dataset_root=str(tmp_path),
        year=None,
        sql="select count(*) as n from income",
        out=None,
        out_format="csv",
    )

    query_cmd.cmd_query(args)

    assert "1" in capsys.readouterr().out
