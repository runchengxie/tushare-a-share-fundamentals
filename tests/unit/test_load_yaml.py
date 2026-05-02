import os
from pathlib import Path

import pytest
import yaml

from tushare_a_fundamentals.config import load_yaml

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]


def test_load_yaml_prefers_yml(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.yml"
    cfg_path.write_text("foo: bar\n", encoding="utf-8")
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))

    data = load_yaml(None)

    assert data == {"foo": "bar"}


def test_load_yaml_supports_yaml(monkeypatch, tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text("answer: 42\n", encoding="utf-8")
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))

    data = load_yaml(None)

    assert data == {"answer": 42}


def test_load_yaml_conflicting_files(monkeypatch, tmp_path):
    (tmp_path / "config.yml").write_text("foo: 1\n", encoding="utf-8")
    (tmp_path / "config.yaml").write_text("foo: 2\n", encoding="utf-8")
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))

    with pytest.raises(SystemExit):
        load_yaml(None)


def test_load_yaml_missing_files_returns_defaults(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))

    data = load_yaml(None)

    captured = capsys.readouterr()
    assert data == {}
    assert "提示：未检测到 config" in captured.out


def test_load_yaml_does_not_auto_load_configs_dir(monkeypatch, tmp_path, capsys):
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "full.yaml").write_text("years: 1\n", encoding="utf-8")
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))

    data = load_yaml(None)

    captured = capsys.readouterr()
    assert data == {}
    assert "config.example.yaml" in captured.out


def test_load_yaml_explicit_configs_path(tmp_path):
    config_path = tmp_path / "configs" / "no_vip.yaml"
    config_path.parent.mkdir()
    config_path.write_text("use_vip: false\n", encoding="utf-8")

    data = load_yaml(str(config_path))

    assert data == {"use_vip": False}


def test_scenario_config_templates_parse():
    names = ["minimal", "full", "no_vip", "audit", "export"]

    for name in names:
        path = ROOT / "configs" / f"{name}.yaml"
        payload = yaml.safe_load(path.read_text("utf-8"))
        assert isinstance(payload, dict)
        assert "token" not in payload
