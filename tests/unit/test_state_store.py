import pytest

from tushare_a_fundamentals.meta import state_store as ss

pytestmark = pytest.mark.unit


def test_init_and_roundtrip(tmp_path):
    db_path = tmp_path / "state.db"
    conn = ss.init_state_store(db_path)
    state = ss.DatasetState(
        dataset="income",
        part_year=2022,
        min_key="2022-01-01",
        max_key="2022-12-31",
        last_checked_at="2023-01-01",
        last_success_at="2023-01-02",
        dirty=1,
    )
    ss.upsert_dataset_state(conn, state)
    fetched = ss.get_dataset_state(conn, "income", 2022)
    assert fetched == state


def test_upsert_overwrites(tmp_path):
    db_path = tmp_path / "state.db"
    conn = ss.init_state_store(db_path)
    base = ss.DatasetState(dataset="income", part_year=2021)
    ss.upsert_dataset_state(conn, base)
    updated = ss.DatasetState(
        dataset="income",
        part_year=2021,
        min_key="a",
        max_key="b",
        last_checked_at="c",
        last_success_at="d",
        dirty=1,
    )
    ss.upsert_dataset_state(conn, updated)
    fetched = ss.get_dataset_state(conn, "income", 2021)
    assert fetched == updated


def test_run_log_roundtrip(tmp_path):
    db_path = tmp_path / "state.db"
    conn = ss.init_state_store(db_path)

    ss.insert_run_log(
        conn,
        run_id="run-1",
        started_at="2026-05-02T00:00:00+00:00",
        status="running",
        config_hash="abc",
    )
    ss.finish_run_log(
        conn,
        run_id="run-1",
        finished_at="2026-05-02T00:01:00+00:00",
        status="success",
    )

    rows = ss.fetch_run_logs(conn)
    assert rows == [
        (
            "run-1",
            "2026-05-02T00:00:00+00:00",
            "2026-05-02T00:01:00+00:00",
            "success",
            "abc",
            None,
        )
    ]
