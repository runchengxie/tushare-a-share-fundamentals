import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

from tushare_a_fundamentals import cli
from tushare_a_fundamentals.commands import download as download_cmd
from tushare_a_fundamentals.dataset_specs import DATASET_SPECS
from tushare_a_fundamentals.meta.doc_fields import DOC_FIELDS

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def _parse_argv(monkeypatch, argv: list[str]):
    monkeypatch.setattr(sys, "argv", argv)
    return cli.parse_cli()


def test_readme_multi_dataset_download_example_parses(monkeypatch):
    args = _parse_argv(
        monkeypatch,
        [
            "funda",
            "download",
            "--datasets",
            "income",
            "balancesheet",
            "cashflow",
            "forecast",
            "express",
            "fina_indicator",
            "fina_audit",
            "fina_mainbz",
            "disclosure_date",
            "--use-vip",
            "--data-dir",
            "data",
            "--since",
            "2010-01-01",
        ],
    )

    assert args.cmd == "download"
    assert args.use_vip is True
    assert "fina_mainbz" in args.datasets


def test_readme_does_not_present_removed_flags_as_current_options():
    readme = (ROOT / "README.md").read_text("utf-8")

    assert "--vip --data-dir" not in readme
    assert "旧版 `--raw-only` 与 `--build-only` 参数已不属于当前 CLI" in readme


def test_config_example_matches_download_defaults():
    config = yaml.safe_load((ROOT / "config.example.yaml").read_text("utf-8"))
    defaults = download_cmd._download_defaults()

    keys = [
        "years",
        "recent_quarters",
        "data_dir",
        "use_vip",
        "max_per_minute",
        "max_retries",
        "state_backend",
        "storage_mode",
        "export_enabled",
        "export_out_format",
        "export_out_dir",
        "export_kinds",
        "export_annual_strategy",
        "export_engine",
    ]
    for key in keys:
        assert config.get(key) == defaults.get(key), key


def test_cli_help_recent_quarters_default_matches_code(monkeypatch, capsys):
    with pytest.raises(SystemExit):
        _parse_argv(monkeypatch, ["funda", "download", "--help"])

    help_text = capsys.readouterr().out
    default_value = download_cmd._download_defaults()["recent_quarters"]
    assert f"默认 {default_value}" in help_text
    assert "默认 8" not in help_text


def test_new_documented_commands_parse(monkeypatch):
    args = _parse_argv(
        monkeypatch,
        ["funda", "query", "select count(*) from income", "--dataset-root", "data"],
    )
    assert args.cmd == "query"
    assert args.sql == "select count(*) from income"

    args = _parse_argv(
        monkeypatch,
        ["funda", "compact", "--dataset-root", "data", "--datasets", "income"],
    )
    assert args.cmd == "compact"
    assert args.datasets == ["income"]

    args = _parse_argv(
        monkeypatch,
        ["funda", "download", "--state-backend", "sqlite", "--storage-mode", "append"],
    )
    assert args.state_backend == "sqlite"
    assert args.storage_mode == "append"


def test_generated_doc_fields_match_committed_docs():
    tool_path = ROOT / "tools" / "update_dataset_fields.py"
    spec = importlib.util.spec_from_file_location("update_dataset_fields", tool_path)
    assert spec and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    generated = {}
    for doc_name, dataset in module.DOC_DATASET_MAP.items():
        doc_path = module.API_DOCS_DIR / doc_name
        fields = module.extract_output_fields(
            doc_path.read_text(encoding="utf-8").splitlines()
        )
        generated[dataset] = tuple(fields)

    assert generated == DOC_FIELDS


def test_dataset_specs_use_generated_fields_and_mainbz_types():
    for dataset, fields in DOC_FIELDS.items():
        assert dataset in DATASET_SPECS
        assert DATASET_SPECS[dataset].fields == ",".join(fields)

    assert tuple(DATASET_SPECS["fina_mainbz"].type_values) == ("P", "D", "I")
