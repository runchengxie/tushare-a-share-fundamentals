# 数据集说明

默认输出目录为 `data/<dataset>/year=YYYY/data.parquet`。主数据始终是 Parquet；SQLite 只用于状态和元数据。下载状态默认写入 `data/_state/state.db`，失败清单写入 `data/_state/failures/`。

每个年度分区会写入 `_manifest.json`，记录 Parquet 文件清单、行数、去重键、schema hash 和更新时间。启用 `storage_mode: append` 时，下载会写入 `part-*.parquet`；可用 `funda compact` 合并去重并恢复紧凑的 `data.parquet` 输出。

表中的“主键”来自 `DatasetSpec.primary_keys`，“去重键”来自 `DatasetSpec.dedup_group_keys`。写入 parquet 时优先按去重键保留最新记录。

| 数据集 | TuShare API | VIP API | 常规下载 | 抓取粒度 | 主键 | 去重键 | 本地字段参考 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `income` | `income` | `income_vip` | 是 | 按报告期（period）逐季抓取；默认 `report_type=1` | `ts_code,end_date,report_type` | `ts_code,end_date` | [income.md](api_references/tushare/income.md) |
| `balancesheet` | `balancesheet` | `balancesheet_vip` | 是 | 按报告期逐季抓取；默认 `report_type=1` | `ts_code,end_date,report_type` | `ts_code,end_date` | [balancesheet.md](api_references/tushare/balancesheet.md) |
| `cashflow` | `cashflow` | `cashflow_vip` | 是 | 按报告期逐季抓取；默认 `report_type=1` | `ts_code,end_date,report_type` | `ts_code,end_date` | [cashflow.md](api_references/tushare/cashflow.md) |
| `forecast` | `forecast` | `forecast_vip` | 是 | 按报告期逐季抓取；`use_vip=false` 时跳过 | `ts_code,end_date,type` | `ts_code,end_date,type` | [forecast.md](api_references/tushare/forecast.md) |
| `express` | `express` | `express_vip` | 是 | 按报告期逐季抓取 | `ts_code,end_date` | `ts_code,end_date` | [express.md](api_references/tushare/express.md) |
| `dividend` | `dividend` | 无 | 否 | 先按公告日期区间尝试，必要时逐日按 `ann_date` 补抓 | `ts_code,ann_date,record_date,ex_date,imp_ann_date` | `ts_code,ann_date,record_date,ex_date,imp_ann_date` | [dividend.md](api_references/tushare/dividend.md) |
| `fina_indicator` | `fina_indicator` | `fina_indicator_vip` | 是 | 按报告期逐季抓取；`use_vip=false` 时跳过 | `ts_code,end_date` | `ts_code,end_date` | [fina_indicator.md](api_references/tushare/fina_indicator.md) |
| `fina_audit` | `fina_audit` | 无 | 否 | 逐股按报告期抓取；默认独立运行最近 1 个季度 | `ts_code,end_date` | `ts_code,end_date` | [fina_audit.md](api_references/tushare/fina_audit.md) |
| `fina_mainbz` | `fina_mainbz` | `fina_mainbz_vip` | 是 | 按报告期和 `type` 抓取；默认 `P,D,I` | `ts_code,end_date,bz_item,type` | `ts_code,end_date,bz_item,type` | [fina_mainbz.md](api_references/tushare/fina_mainbz.md) |
| `disclosure_date` | `disclosure_date` | 无 | 是 | 按季度 `end_date` 抓取 | `ts_code,end_date,ann_date,pre_date,actual_date` | `ts_code,end_date` | [disclosure_date.md](api_references/tushare/disclosure_date.md) |

## 默认选择

常规 `funda download` 会运行：

```text
income, balancesheet, cashflow, forecast, express,
fina_indicator, fina_mainbz, disclosure_date
```

`dividend` 和 `fina_audit` 默认跳过，因为两者耗时明显更长：

- `dividend`：使用 `funda download --dividend-only` 单独下载。
- `fina_audit`：使用 `funda download --audit-only` 单独下载，或用 `--with-audit` 追加到常规任务。
- `--all`：按配置和内建默认补齐全部数据集，包含 `dividend` 和 `fina_audit`。

## 报表类型

三张财务报表支持 `report_type`。项目默认下载 `1`，即合并报表。可在配置文件中设置 `report_types`，也可在命令行使用 `--report-types 6` 下载母公司报表。

| 代码 | 类型 | 说明 |
| --- | --- | --- |
| `1` | 合并报表 | 上市公司最新合并报表，项目默认值 |
| `2` | 单季合并 | 单一季度的合并报表 |
| `3` | 调整单季合并表 | 调整后的单季合并报表 |
| `4` | 调整合并报表 | 本年度公布上年同期的财务报表数据，报告期为上年度 |
| `5` | 调整前合并报表 | 数据发生变更时保留的调整前数据 |
| `6` | 母公司报表 | 母公司的财务报表数据 |
| `7` | 母公司单季表 | 母公司的单季度表 |
| `8` | 母公司调整单季表 | 母公司调整后的单季表 |
| `9` | 母公司调整表 | 母公司本年度公布上年同期的财务报表数据 |
| `10` | 母公司调整前报表 | 母公司调整前的原始报表 |
| `11` | 母公司调整前合并报表 | 母公司调整前的合并报表原数据 |
| `12` | 母公司调整前报表 | 母公司报表发生变更前保留的原数据 |

## 主营业务构成类型

`fina_mainbz.type` 支持三种取值：

- `P`：按产品。
- `D`：按地区。
- `I`：按行业。

配置示例：

```yaml
datasets:
  - name: fina_mainbz
    type: ["P", "D"]
```

## TuShare 官方文档

- [利润表](https://tushare.pro/document/2?doc_id=33)
- [资产负债表](https://tushare.pro/document/2?doc_id=36)
- [现金流量表](https://tushare.pro/document/2?doc_id=44)
- [业绩预告](https://tushare.pro/document/2?doc_id=45)
- [业绩快报](https://tushare.pro/document/2?doc_id=46)
- [分红送股](https://tushare.pro/document/2?doc_id=103)
- [财务指标数据](https://tushare.pro/document/2?doc_id=79)
- [财务审计意见](https://tushare.pro/document/2?doc_id=80)
- [主营业务构成](https://tushare.pro/document/2?doc_id=81)
- [财报披露计划](https://tushare.pro/document/2?doc_id=162)
