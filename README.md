# TuShare A 股基本面数据下载器

本项目提供 `funda` 命令，用于批量下载 A 股上市公司基本面数据，按数据集（dataset）写入 parquet 缓存，并可导出 CSV 或 parquet 文件。

项目默认面向全 A 市场批量下载，建议使用 5000 积分以上的 TuShare VIP 账户。`use_vip=false` 时会跳过仅支持 VIP 批量抓取的数据集；项目当前没有实现这些接口的逐股回退抓取。

## 功能概览

- 支持 10 类 TuShare 基本面数据集：三张财务报表、业绩预告、业绩快报、分红、财务指标、审计意见、主营业务构成、财报披露计划。
- 默认下载近 10 年季度数据，并滚动刷新最近 4 个季度。
- 输出目录默认为 `data/<dataset>/year=YYYY/data.parquet`。
- 增量状态默认为 JSON 文件：`data/_state/state.json`。
- 失败清单写入 `data/_state/failures/`，便于后续排查和补跑。
- 可在下载后运行 `funda export`，生成平面表和 `income` 的年度、季度累计、单季口径导出。

## 适用前提

- Python 3.10 到 3.12。
- 有效的 TuShare token。全市场批量抓取建议使用 5000 积分以上的 VIP token。
- 可写磁盘空间和稳定网络。
- 可选：安装 `direnv`，自动加载 `.env` 和本地虚拟环境。

## 安装

```bash
uv sync
```

也可以使用 pip 可编辑安装：

```bash
pip install -e .
```

安装后检查 CLI：

```bash
funda --help
```

## 快速开始

```bash
export TUSHARE_TOKEN="your-token"

funda download
funda export --dataset-root data --out-dir data/export
```

如果使用 `.env` 文件，请配合 `direnv` 加载：

```bash
cp .env.example .env
cp .envrc.example .envrc
direnv allow
```

`funda download` 默认下载常用数据集，跳过耗时较长的 `dividend` 和 `fina_audit`，并且只写 parquet 缓存。需要下载这两个数据集时建议单独执行：

```bash
funda download --dividend-only
funda download --audit-only
```

## 常用命令

| 任务 | 命令 |
| --- | --- |
| 下载默认数据集 | `funda download` |
| 指定时间范围 | `funda download --since 2010-01-01 --until 2024-12-31` |
| 下载指定数据集 | `funda download --datasets income balancesheet cashflow` |
| 下载分红数据 | `funda download --dividend-only` |
| 下载审计意见 | `funda download --audit-only` |
| 下载完成后立即导出 | `funda download --export --export-kinds annual,single,cumulative` |
| 导出已有缓存 | `funda export --dataset-root data --out-dir data/export` |
| 查看状态 | `funda state show --backend json --data-dir data` |
| 查看失败清单 | `funda state ls-failures --data-dir data` |
| 查看帮助 | `funda download --help` |

## 默认行为

- 时间窗口：近 10 年，约 40 个季度；命令行优先级为 `--since/--until`、`--quarters`、`--years`。
- 刷新策略：补齐历史缺口，并重抓最近 `recent_quarters` 个季度；默认值为 4。
- VIP 接口：默认启用。未检测到 5000 积分以上 token 时，常规批量下载会报错退出。
- 常规下载：默认包含 `income`、`balancesheet`、`cashflow`、`forecast`、`express`、`fina_indicator`、`fina_mainbz`、`disclosure_date`。
- 单独下载：`dividend` 逐日抓取，`fina_audit` 逐股抓取，默认不随常规下载运行。
- 导出：默认不自动导出；使用 `--export` 或单独运行 `funda export`。
- 状态：下载流程目前使用 JSON 状态文件；SQLite 后端只用于 `funda state` 的查看和维护操作。
- 旧版 `--raw-only` 与 `--build-only` 参数已不属于当前 CLI。

## 文档

- [使用流程](docs/usage.md)：下载、覆盖率检查、进度展示和常用命令。
- [配置说明](docs/configuration.md)：`config.yml`、`.env`、token 和导出配置。
- [数据集说明](docs/datasets.md)：数据集、TuShare API、主键、去重键和抓取粒度。
- [导出说明](docs/export.md)：平面导出、`income` 派生口径、压缩和按年拆分。
- [状态与失败清单](docs/state.md)：JSON 状态、SQLite 维护后端和失败记录。
- [开发说明](docs/development.md)：测试、字段生成和维护脚本。

## 开发

```bash
pytest
pytest -m unit
pytest -m integration
ruff check .
ruff format .
```

README 中只保留上手所需内容。完整参数以 `funda <command> --help` 和 `docs/` 文档为准。
