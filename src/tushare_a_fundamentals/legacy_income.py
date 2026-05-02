"""Deprecated compatibility entry points for the old income raw workflow."""

from __future__ import annotations

import warnings
from typing import Any


def _warn(name: str) -> None:
    warnings.warn(
        f"{name} belongs to the legacy income/raw workflow and will be removed "
        "after the compatibility window. Use `funda download` and `funda export`.",
        DeprecationWarning,
        stacklevel=2,
    )


def fetch_income_bulk(*args: Any, **kwargs: Any):
    _warn("fetch_income_bulk")
    from .common import fetch_income_bulk as _impl

    return _impl(*args, **kwargs)


def save_tables(*args: Any, **kwargs: Any):
    _warn("save_tables")
    from .common import save_tables as _impl

    return _impl(*args, **kwargs)


def run_bulk_mode(*args: Any, **kwargs: Any):
    _warn("_run_bulk_mode")
    from .common import _run_bulk_mode as _impl

    return _impl(*args, **kwargs)
