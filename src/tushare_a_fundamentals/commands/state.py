from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

from ..common import eprint
from ..state_backend import (
    StateBackend,
    open_state_backend,
    resolve_state_backend,
)


def _resolve_backend_and_path(args: argparse.Namespace) -> tuple[str, Path]:
    resolved = resolve_state_backend(
        backend=args.backend,
        state_path=args.state_path,
        data_dir=args.data_dir or "data",
    )
    return resolved.backend, resolved.path


def _ls_failures(data_dir: Path) -> None:
    root = data_dir / "_state" / "failures"
    if not root.exists():
        print("未发现失败记录目录")
        return
    files: Iterable[Path] = sorted(root.glob("*.json"))
    found = False
    for fp in files:
        found = True
        try:
            payload = json.loads(fp.read_text("utf-8"))
            entries = payload.get("entries", [])
            print(f"{fp}: {len(entries)} 条记录")
        except json.JSONDecodeError:
            print(f"{fp}: 无法解析（可能损坏）")
    if not found:
        print("未发现失败记录文件")


def cmd_state(args: argparse.Namespace) -> None:
    data_dir = Path(args.data_dir or "data")

    if args.action == "ls-failures":
        _ls_failures(data_dir)
        return

    backend_impl: StateBackend
    resolved = resolve_state_backend(
        backend=args.backend,
        state_path=args.state_path,
        data_dir=data_dir,
    )
    backend_impl = open_state_backend(resolved)

    if args.action == "show":
        result = backend_impl.snapshot(args.dataset)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.action == "clear":
        if not args.dataset:
            eprint("错误：清理状态时必须指定 --dataset")
            return
        backend_impl.delete(args.dataset, args.key, year=args.year)
        target = [f"dataset={args.dataset}"]
        if args.key:
            target.append(f"key={args.key}")
        if args.year is not None:
            target.append(f"year={args.year}")
        print(f"已清理状态：{', '.join(target)}")
        return

    if args.action == "set":
        if not args.dataset or not args.key or args.value is None:
            eprint("错误：设置状态时必须提供 --dataset、--key、--value")
            return
        backend_impl.set(args.dataset, args.key, args.value)
        print(f"已更新状态：{args.dataset}.{args.key} = {args.value}")
        return

    eprint(f"错误：未识别的操作 {args.action}")


def register_state_subparser(subparsers: argparse._SubParsersAction) -> None:
    sp = subparsers.add_parser("state", help="查看与维护增量状态信息")
    sp.set_defaults(cmd="state")
    sp.add_argument(
        "action",
        choices=["show", "clear", "set", "ls-failures"],
        help="操作类型",
    )
    sp.add_argument("--backend", choices=["auto", "json", "sqlite"], default="auto")
    sp.add_argument(
        "--state-backend",
        dest="backend",
        choices=["auto", "json", "sqlite"],
        help="状态后端别名：auto/json/sqlite",
    )
    sp.add_argument("--state-path", help="状态文件或数据库路径")
    sp.add_argument("--data-dir", default="data", help="多数据集数据目录（默认 data）")
    sp.add_argument("--dataset", help="目标数据集名称")
    sp.add_argument("--year", type=int, help="针对 SQLite 状态时可指定年份分区")
    sp.add_argument("--key", help="状态键名")
    sp.add_argument("--value", help="状态值")
