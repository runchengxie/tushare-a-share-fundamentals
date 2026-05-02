# 使用流程

## 准备 token

CLI 读取 shell 环境变量或 `--token` 参数。它不会自动读取 `.env` 文件。推荐使用其中一种方式：

```bash
export TUSHARE_TOKEN="your-token"
```

或使用 `direnv`：

```bash
cp .env.example .env
cp .envrc.example .envrc
direnv allow
```

## 下载数据

默认下载近 10 年常用数据集：

```bash
funda download
```

根目录 `config.yml` 或 `config.yaml` 会被自动读取。场景模板位于 `configs/`，例如：

```bash
cp configs/minimal.yaml config.yml
funda download --config configs/no_vip.yaml
```

按日期范围下载：

```bash
funda download --since 2010-01-01
funda download --since 2010-01-01 --until 2024-12-31
```

按季度数或年数下载：

```bash
funda download --quarters 40
funda download --years 5
```

时间窗口优先级为：

```text
--since/--until > --quarters > --years
```

所有周期型数据集按季度期末日抓取，取值为 `0331`、`0630`、`0930`、`1231`。

## 选择数据集

```bash
funda download --datasets income balancesheet cashflow forecast express
```

常用开关：

| 参数 | 说明 |
| --- | --- |
| `--datasets ...` | 只运行传入的数据集列表 |
| `--dividend-only` | 只下载 `dividend` |
| `--audit-only` | 只下载 `fina_audit`；未指定窗口时默认最近 1 个季度 |
| `--with-audit` | 在常规下载中追加 `fina_audit` |
| `--all` | 包含内建默认中的全部数据集，含 `dividend` 和 `fina_audit` |
| `--data-dir DIR` | 设置多数据集输出目录，默认 `data` |

`dividend` 需要按公告日期逐日补抓，`fina_audit` 需要逐股循环，建议在常规批量下载之外单独执行。

## VIP 与限速

`download` 默认启用 VIP 接口。未检测到 5000 积分以上 token 时，常规批量下载会报错退出。

```bash
funda download --max-per-minute 60
```

如果确实要使用普通接口，可在 `config.yml` 中设置：

```yaml
use_vip: false
```

此时 `forecast`、`fina_indicator`、`fina_mainbz` 会被跳过。

## 滚动刷新

默认补齐历史缺口，并重抓最近 4 个季度，以吸收财报修订和披露日期变化。

```bash
funda download --recent-quarters 2
funda download --recent-quarters 0
```

`--recent-quarters 0` 表示只补缺。

## 报表类型

三张财务报表默认下载 `report_type=1`。

```bash
funda download --report-types 1,6
```

完整取值见 [datasets.md](datasets.md#报表类型)。

## 进度展示

下载和导出都支持进度模式：

```bash
funda download --progress auto
funda download --progress rich
funda download --progress plain
funda download --progress none
funda export --progress plain
```

`auto` 会在 TTY 下使用 Rich 进度条，在 CI 或重定向日志时使用纯文本进度。

## 覆盖率检查

```bash
funda coverage --dataset-root data
funda coverage --dataset-root data --by period
funda coverage --dataset-root data --csv data/coverage_gaps.csv
funda coverage --dataset-root data --engine duckdb
```

当前 `coverage` 命令读取以下旧版 `income` 派生目录：

```text
dataset=inventory_income/periods.parquet
dataset=fact_income_cum/
```

新版 `funda download` 生成的 `income/` 分区不会被 `coverage` 扫描。只有在目录中已经存在上述派生数据时，`coverage` 才能输出有效结果。

## 查询和 compact

主数据保持为 Parquet。安装可选 DuckDB 后，可以直接查询本地数据集：

```bash
funda query "select ts_code, end_date from income limit 10" --dataset-root data
funda export --dataset-root data --engine duckdb
```

默认写入模式是 `compact`，每个年度分区生成 `data.parquet`。如果启用 append 写入：

```bash
funda download --storage-mode append
```

后续可合并并去重：

```bash
funda compact --dataset-root data --datasets income --years 2024
```

每个年度分区会维护 `_manifest.json`，记录文件清单、行数、去重键、schema hash 和更新时间。

## 旧版目录

当前多数据集流程默认使用 `data/`。历史流程使用 `out/`，如需读取旧目录，可在相关命令中显式传入：

```bash
funda export --dataset-root out --out-dir out/export
funda coverage --dataset-root out
```

旧版 `--raw-only` 和 `--build-only` 参数已经不属于当前 CLI。推荐流程是先运行 `funda download` 写入 parquet 缓存，再运行 `funda export` 构建导出文件。
