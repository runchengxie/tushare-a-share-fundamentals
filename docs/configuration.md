# 配置说明

## 配置文件

根目录可放置一个配置文件：

```text
config.yml
config.yaml
```

两者同时存在时，CLI 会报错并要求只保留一个。没有配置文件时，`funda download` 使用内建默认值，并提示可从模板复制：

```bash
cp config.example.yaml config.yml
```

命令行参数优先级高于配置文件。

`configs/` 目录提供场景化模板，但不会被自动加载。需要使用时可以复制到根目录，或通过 `--config` 显式指定：

```bash
cp configs/full.yaml config.yml
funda download --config configs/no_vip.yaml
```

| 模板 | 用途 |
| --- | --- |
| `configs/minimal.yaml` | 最小可运行配置 |
| `configs/full.yaml` | 全数据集配置 |
| `configs/no_vip.yaml` | 非 VIP token 配置 |
| `configs/audit.yaml` | 审计意见单独抓取配置 |
| `configs/export.yaml` | 下载后自动导出配置 |

## 环境变量

`funda` 读取 shell 环境变量或 `--token` 参数。它不会自动读取 `.env` 文件。使用 `.env` 时请配合 `direnv`，或把变量导出到当前 shell。

```bash
export TUSHARE_TOKEN="your-token"
```

支持的变量：

| 变量 | 说明 |
| --- | --- |
| `TUSHARE_TOKEN` | 主 token，常规使用必填 |
| `TUSHARE_TOKEN_2` | 第二个 token，用于轮询调用 |
| `TUSHARE_VIP_TOKENS` | 逗号分隔的 VIP token 列表，用于显式指定 VIP 凭证 |
| `TUSHARE_DETECT_VIP` | 设为 `false`、`0`、`no` 或 `off` 可关闭自动积分检测 |

部分旧兼容代码会识别 `TUSHARE_API_KEY`。当前 `funda` CLI 入口请使用 `TUSHARE_TOKEN` 或 `--token`。

## 最小配置

```yaml
years: 10
recent_quarters: 4
data_dir: "data"
use_vip: true
max_per_minute: 90
max_retries: 3
state_backend: "auto"
storage_mode: "compact"
```

## 数据集配置

```yaml
datasets:
  - name: income
    report_types: [1]
  - name: balancesheet
    report_types: [1]
  - name: cashflow
    report_types: [1]
  - name: forecast
  - name: express
  - name: fina_indicator
  - name: fina_mainbz
    type: ["P", "D", "I"]
  - name: disclosure_date
```

`dividend` 和 `fina_audit` 可以写入配置，但常规下载会按默认策略跳过。使用 `--dividend-only`、`--audit-only`、`--with-audit` 或 `--all` 显式启用。

## 时间窗口

```yaml
years: 10
# quarters: 40
audit_quarters: 1
# audit_years: 1
recent_quarters: 4
```

规则：

- `years: 10` 表示最近约 40 个季度。
- `quarters` 可直接指定季度数。
- `--since/--until`、`quarters`、`years` 按这个顺序决定窗口。
- `audit_quarters` 和 `audit_years` 只影响 `--audit-only`。
- `recent_quarters` 控制滚动刷新窗口；设为 0 时只补缺。

## 状态路径

```yaml
state_backend: "auto"
state_path: null
```

`state_backend` 可选 `auto`、`json`、`sqlite`。`auto` 模式下，新数据目录默认写入 `<data_dir>/_state/state.db`；如果检测到旧 `<data_dir>/_state/state.json` 且没有 SQLite 状态库，会复制迁移到 SQLite，原 JSON 文件不会删除。

`state_path` 可覆盖默认路径。后缀为 `.db` 时选择 SQLite，其他后缀选择 JSON。显式 `state_backend: json` 可继续使用 `<data_dir>/_state/state.json`。

详见 [state.md](state.md)。

## 存储模式

```yaml
storage_mode: "compact"
```

`storage_mode` 可选：

| 值 | 说明 |
| --- | --- |
| `compact` | 默认兼容行为，写入后生成 `year=YYYY/data.parquet` 并刷新 manifest |
| `append` | 写入 `part-*.parquet`，后续通过 `funda compact` 合并去重 |

## 字段清单

多数据集下载的字段清单来自 `docs/api_references/tushare/`，并生成到：

```text
src/tushare_a_fundamentals/meta/doc_fields.py
```

通常不需要在配置文件中设置全局 `fields`。如需更新字段，先调整本地 TuShare 字段参考，再运行字段生成脚本。

## 下载后自动导出

默认只写 parquet 缓存：

```yaml
export_enabled: false
```

启用自动导出：

```yaml
export_enabled: true
export_out_format: "csv"
export_out_dir: null
export_kinds: "annual,single,cumulative"
export_annual_strategy: "cumulative"
export_engine: "pandas"
```

常用导出配置：

| 配置 | 说明 |
| --- | --- |
| `export_out_format` | `csv` 或 `parquet` |
| `export_out_dir` | 导出根目录；留空时使用 `data_dir` |
| `export_kinds` | `income` 派生口径，逗号分隔 |
| `export_flat_datasets` | `auto`、`all`、`none` 或数据集列表 |
| `export_flat_exclude` | 逗号分隔的排除列表 |
| `export_split_by` | `none` 或 `year` |
| `export_gzip` | CSV 输出为 `.csv.gz` |
| `export_no_income` | 跳过 `income` 派生导出 |
| `export_no_flat` | 跳过平面导出 |
| `export_years` | 导出最近 N 年 |
| `export_strict` | 导出失败时让 `download` 返回错误 |
| `export_engine` | `pandas` 或 `duckdb`，默认 `pandas` |
