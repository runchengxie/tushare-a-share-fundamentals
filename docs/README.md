# 文档索引

本目录保存两类文档：

- 项目级文档：说明本项目如何组织 dataset、CLI 输出、状态和字段生成。
- TuShare API 文档：保留接口字段表，供 `tools/update_dataset_fields.py` 生成字段映射。

## 项目文档

- [datasets.md](datasets.md)：dataset 名称、TuShare API、输出路径、主键和特殊抓取方式。

## 字段生成

`tools/update_dataset_fields.py` 会解析本目录下的 TuShare API 文档，并生成：

```text
src/tushare_a_fundamentals/meta/doc_fields.py
```

修改 API 字段表后，应运行：

```bash
uv run tools/update_dataset_fields.py
```

只校验解析是否成功时，运行：

```bash
uv run tools/update_dataset_fields.py --check
```

## 维护脚本

- `tools/update_dataset_fields.py`：可重复运行的字段映射生成器。
- `project_tools/verify_tushare_tokens.py`：检查一个或多个 TuShare token 的积分和 VIP 可用性。
- `project_tools/check_api_availability.py`：人工诊断单个 TuShare API 是否可用，适合排查接口权限或字段问题。
- `project_tools/export_repo_source.py`：导出源码快照，供离线审阅使用。
- `project_tools/package.sh`：维护者打包辅助脚本。

## TuShare API 文档

| 项目 dataset | 文档 |
| --- | --- |
| `income` | [income_statement_tushare_api_doc.md](income_statement_tushare_api_doc.md) |
| `balancesheet` | [balance_sheet_tushare_api_doc.md](balance_sheet_tushare_api_doc.md) |
| `cashflow` | [cash_flow_statement_tushare_api_doc.md](cash_flow_statement_tushare_api_doc.md) |
| `forecast` | [earnings_preannouncement_tushare_api_doc.md](earnings_preannouncement_tushare_api_doc.md) |
| `express` | [preliminary_unaudited_results_tushare_api_doc.md](preliminary_unaudited_results_tushare_api_doc.md) |
| `dividend` | [dividend_info_tushare_api_doc.md](dividend_info_tushare_api_doc.md) |
| `fina_indicator` | [financial_ratios_tushare_api_doc.md](financial_ratios_tushare_api_doc.md) |
| `fina_audit` | [audit_opinion_tushare_api_doc.md](audit_opinion_tushare_api_doc.md) |
| `fina_mainbz` | [revenue_breakdown_tushare_api_doc.md](revenue_breakdown_tushare_api_doc.md) |
| `disclosure_date` | [release_date_tushare_api_doc.md](release_date_tushare_api_doc.md) |
