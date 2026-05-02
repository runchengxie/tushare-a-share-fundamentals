# 数据集映射

默认输出目录为 `data/<dataset>/year=YYYY/part-*.parquet`。增量状态默认写入 `data/_state/state.json`。失败记录写入 `data/_state/failures/`。

| dataset | TuShare API | VIP API | 默认常规下载 | 特殊抓取方式 | 主键 / 去重键 | API 文档 |
| --- | --- | --- | --- | --- | --- | --- |
| `income` | `income` | `income_vip` | 是 | 按季度 period 抓取；默认 `report_type=1` | `ts_code,end_date,report_type` | `income_statement_tushare_api_doc.md` |
| `balancesheet` | `balancesheet` | `balancesheet_vip` | 是 | 按季度 period 抓取；默认 `report_type=1` | `ts_code,end_date,report_type` | `balance_sheet_tushare_api_doc.md` |
| `cashflow` | `cashflow` | `cashflow_vip` | 是 | 按季度 period 抓取；默认 `report_type=1` | `ts_code,end_date,report_type` | `cash_flow_statement_tushare_api_doc.md` |
| `forecast` | `forecast` | `forecast_vip` | 是 | 按季度 period 抓取；`use_vip=false` 时跳过 | `ts_code,end_date,type` | `earnings_preannouncement_tushare_api_doc.md` |
| `express` | `express` | `express_vip` | 是 | 按季度 period 抓取 | `ts_code,end_date` | `preliminary_unaudited_results_tushare_api_doc.md` |
| `dividend` | `dividend` | 无 | 否 | 逐日按 `ann_date` 抓取；用 `--dividend-only` 单独运行 | `ts_code,ann_date,record_date,ex_date,imp_ann_date` | `dividend_info_tushare_api_doc.md` |
| `fina_indicator` | `fina_indicator` | `fina_indicator_vip` | 是 | 按季度 period 抓取；`use_vip=false` 时跳过 | `ts_code,end_date` | `financial_ratios_tushare_api_doc.md` |
| `fina_audit` | `fina_audit` | 无 | 否 | 逐股按 period 抓取；用 `--audit-only` 或 `--with-audit` 启用 | `ts_code,end_date` | `audit_opinion_tushare_api_doc.md` |
| `fina_mainbz` | `fina_mainbz` | `fina_mainbz_vip` | 是 | 按季度 period 和 `type` 抓取；默认 `P,D,I` | `ts_code,end_date,bz_item,type` | `revenue_breakdown_tushare_api_doc.md` |
| `disclosure_date` | `disclosure_date` | 无 | 是 | 按季度 end_date 抓取 | `ts_code,end_date` | `release_date_tushare_api_doc.md` |

## 默认与显式启用

常规 `funda download` 会跳过 `dividend` 和 `fina_audit`，因为它们耗时明显更长：

- `dividend` 使用 `funda download --dividend-only` 单独下载。
- `fina_audit` 使用 `funda download --audit-only` 单独下载，或用 `--with-audit` 追加到常规任务。
- `--all` 会按配置包含全部数据集，包括 `dividend` 和 `fina_audit`。

## `fina_mainbz` type

`fina_mainbz.type` 支持：

- `P`：按产品
- `D`：按地区
- `I`：按行业

默认配置会下载三种类型。可在 `config.yaml` 中缩小范围，例如：

```yaml
datasets:
  - name: fina_mainbz
    type: ["P", "D"]
```
