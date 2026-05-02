# 开发说明

## 项目结构

- `src/tushare_a_fundamentals/`：库代码和 CLI 实现。
- `src/tushare_a_fundamentals/commands/`：`download`、`export`、`coverage`、`state` 子命令。
- `src/tushare_a_fundamentals/dataset_specs.py`：数据集定义、主键、去重键和抓取方式。
- `docs/api_references/tushare/`：TuShare 字段参考。
- `tests/unit/`：单元测试。
- `tests/integration/`：集成测试。
- `tools/`：可重复运行的项目工具。
- `project_tools/`：维护者诊断和打包脚本。

## 安装依赖

```bash
uv sync
```

或：

```bash
pip install -e .
```

## 测试和格式

```bash
pytest
pytest -m unit
pytest -m integration
ruff check .
ruff format .
```

提交前至少运行与改动相关的 pytest marker 和 Ruff 检查。README 中出现的命令示例如果描述了支持流程，应补 CLI 解析或烟测覆盖。

## 字段生成

字段清单从 `docs/api_references/tushare/` 生成到：

```text
src/tushare_a_fundamentals/meta/doc_fields.py
```

更新字段参考后运行：

```bash
uv run tools/update_dataset_fields.py
```

只校验解析：

```bash
uv run tools/update_dataset_fields.py --check
```

## 维护脚本

- `tools/update_dataset_fields.py`：字段映射生成器。
- `project_tools/verify_tushare_tokens.py`：检查 token 积分和 VIP 可用性。
- `project_tools/check_api_availability.py`：诊断单个 TuShare API。
- `project_tools/export_repo_source.py`：导出源码快照。
- `project_tools/package.sh`：打包辅助脚本。

## 文档维护要点

- CLI 参数以 `src/tushare_a_fundamentals/cli.py` 为准。
- 数据集事实以 `src/tushare_a_fundamentals/dataset_specs.py` 为准。
- 下载状态事实以 `src/tushare_a_fundamentals/downloader.py` 和 `commands/state.py` 为准。
- 涉及 TuShare API 字段时，同步更新本地字段参考和生成文件。
