"""Configuration parsing helpers for CLI commands."""

from __future__ import annotations

import os
import sys
from typing import Any, Optional

import yaml


def eprint(msg: str) -> None:
    print(msg, file=sys.stderr)


def load_yaml(path: Optional[str]) -> dict:
    def _read(candidate: str) -> dict:
        try:
            with open(candidate, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                print(f"已加载配置文件：{candidate}")
                return cfg
        except FileNotFoundError:
            eprint(f"错误：未找到配置文件 {candidate}")
            sys.exit(2)
        except Exception as exc:
            eprint(f"错误：读取配置文件失败：{exc}")
            sys.exit(2)

    if path:
        return _read(path)

    cwd = os.getcwd()
    candidates = [
        os.path.join(cwd, "config.yml"),
        os.path.join(cwd, "config.yaml"),
    ]
    existing = [candidate for candidate in candidates if os.path.exists(candidate)]
    if not existing:
        print(
            "提示：未检测到 config.yml/config.yaml，将使用内建默认值。"
            "可通过 'cp config.example.yaml config.yml' 进行自定义"
        )
        return {}
    if len(existing) > 1:
        eprint(
            "错误：检测到 config.yml 与 config.yaml 同时存在，请保留一个以保证唯一事实"
        )
        sys.exit(2)
    return _read(existing[0])


def merge_config(cli: dict | None, cfg: dict | None, defaults: dict | None) -> dict:
    merged: dict = {**(defaults or {}), **(cfg or {})}
    if not cli:
        return merged
    for key, value in cli.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        merged[key] = value
    return merged


def normalize_fields(value: Any) -> Optional[str]:
    """Normalize a ``fields`` configuration value."""

    if value is None:
        return None
    if isinstance(value, str):
        trimmed = value.strip()
        return trimmed or None
    if isinstance(value, (list, tuple, set)):
        items = [str(item).strip() for item in value if str(item).strip()]
        if not items:
            return None
        return ",".join(items)
    return None


def parse_report_types(value: Any) -> list[int]:
    """Parse ``report_types`` config into a list of ints."""

    if value is None:
        return [1]
    if isinstance(value, list):
        return [int(item) for item in value]
    if isinstance(value, (int, float)):
        return [int(value)]
    if isinstance(value, str):
        return [int(item) for item in value.split(",") if item.strip()]
    return [1]
