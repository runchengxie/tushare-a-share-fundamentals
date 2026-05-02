import json
from argparse import Namespace

import pytest

from tushare_a_fundamentals.commands import state as state_cmd

pytestmark = pytest.mark.unit


def make_args(**kwargs):
    defaults = dict(
        action="show",
        backend="auto",
        state_path=None,
        data_dir="data",
        dataset=None,
        year=None,
        key=None,
        value=None,
    )
    defaults.update(kwargs)
    return Namespace(**defaults)


def test_state_show_json(tmp_path, capsys):
    data_dir = tmp_path / "data"
    state_file = data_dir / "_state" / "state.json"
    state_file.parent.mkdir(parents=True)
    state_file.write_text(json.dumps({"income": {"last_period": "20231231"}}), "utf-8")

    args = make_args(
        action="show", backend="json", state_path=None, data_dir=str(data_dir)
    )
    state_cmd.cmd_state(args)

    captured = capsys.readouterr()
    assert "20231231" in captured.out


def test_state_clear_json(tmp_path):
    data_dir = tmp_path / "data"
    state_file = data_dir / "_state" / "state.json"
    state_file.parent.mkdir(parents=True)
    state_file.write_text(json.dumps({"income": {"foo": "bar"}}), "utf-8")

    args = make_args(
        action="clear",
        backend="json",
        state_path=None,
        data_dir=str(data_dir),
        dataset="income",
        key="foo",
    )
    state_cmd.cmd_state(args)

    payload = json.loads(state_file.read_text("utf-8"))
    assert payload == {}


def test_state_set_json(tmp_path, capsys):
    data_dir = tmp_path / "data"
    args = make_args(
        action="set",
        backend="json",
        data_dir=str(data_dir),
        dataset="income",
        key="last_period",
        value="20231231",
    )
    state_cmd.cmd_state(args)
    capsys.readouterr()

    state_file = data_dir / "_state" / "state.json"
    payload = json.loads(state_file.read_text("utf-8"))
    assert payload == {"income": {"last_period": "20231231"}}


def test_state_ls_failures(tmp_path, capsys):
    data_dir = tmp_path / "data"
    failure_dir = data_dir / "_state" / "failures"
    failure_dir.mkdir(parents=True)
    sample = {
        "dataset": "income",
        "entries": [{"period": "20231231"}],
    }
    (failure_dir / "income_periods.json").write_text(json.dumps(sample), "utf-8")

    args = make_args(action="ls-failures", data_dir=str(data_dir))
    state_cmd.cmd_state(args)

    captured = capsys.readouterr()
    assert "income_periods.json" in captured.out
    assert "1 条记录" in captured.out


def test_state_set_sqlite(tmp_path, capsys):
    db_path = tmp_path / "state.db"
    args_set = make_args(
        action="set",
        backend="sqlite",
        state_path=str(db_path),
        dataset="income",
        key="last_period",
        value="20231231",
    )
    state_cmd.cmd_state(args_set)
    capsys.readouterr()

    args_show = make_args(
        action="show",
        backend="sqlite",
        state_path=str(db_path),
    )
    state_cmd.cmd_state(args_show)
    captured = capsys.readouterr()
    assert "kv_state" in captured.out
    assert "20231231" in captured.out


def test_state_clear_sqlite_key(tmp_path, capsys):
    db_path = tmp_path / "state.db"
    args_set = make_args(
        action="set",
        backend="sqlite",
        state_path=str(db_path),
        dataset="income",
        key="last_period",
        value="20231231",
    )
    state_cmd.cmd_state(args_set)
    capsys.readouterr()

    args_clear = make_args(
        action="clear",
        backend="sqlite",
        state_path=str(db_path),
        dataset="income",
        key="last_period",
    )
    state_cmd.cmd_state(args_clear)
    capsys.readouterr()

    args_show = make_args(action="show", backend="sqlite", state_path=str(db_path))
    state_cmd.cmd_state(args_show)
    captured = capsys.readouterr()
    assert "20231231" not in captured.out


def test_state_backend_auto_prefers_sqlite(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    db_path = data_dir / "_state" / "state.db"
    db_path.parent.mkdir(parents=True)
    db_path.write_bytes(b"")

    args = make_args(data_dir=str(data_dir))
    monkeypatch.chdir(tmp_path)

    backend, path = state_cmd._resolve_backend_and_path(args)

    assert backend == "sqlite"
    assert path == db_path


def test_state_backend_auto_defaults_to_sqlite(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    args = make_args(data_dir=str(data_dir))

    monkeypatch.chdir(tmp_path)

    backend, path = state_cmd._resolve_backend_and_path(args)

    assert backend == "sqlite"
    assert path == data_dir / "_state" / "state.db"


def test_state_backend_auto_migrates_json(tmp_path, capsys):
    data_dir = tmp_path / "data"
    json_path = data_dir / "_state" / "state.json"
    json_path.parent.mkdir(parents=True)
    json_path.write_text(json.dumps({"income": {"last_period": "20231231"}}), "utf-8")

    args = make_args(action="show", backend="auto", data_dir=str(data_dir))
    state_cmd.cmd_state(args)

    captured = capsys.readouterr()
    assert "kv_state" in captured.out
    assert "20231231" in captured.out
    assert json_path.exists()
    assert (data_dir / "_state" / "state.db").exists()


def test_state_backend_auto_uses_suffix(tmp_path):
    db_path = tmp_path / "custom.db"
    json_path = tmp_path / "custom.json"

    backend, path = state_cmd._resolve_backend_and_path(
        make_args(backend="auto", state_path=str(db_path))
    )
    assert backend == "sqlite"
    assert path == db_path

    backend, path = state_cmd._resolve_backend_and_path(
        make_args(backend="auto", state_path=str(json_path))
    )
    assert backend == "json"
    assert path == json_path
