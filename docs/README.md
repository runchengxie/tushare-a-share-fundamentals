# 文档索引

本目录保存两类文档：

- 项目级文档：位于 `docs/` 根目录，说明本项目如何组织 dataset、CLI 输出、状态和字段生成。
- TuShare API 参考资料：位于 `docs/api_references/tushare/`，保留外部接口字段表，供 `tools/update_dataset_fields.py` 生成字段映射。

## 项目文档

- [datasets.md](datasets.md)：dataset 名称、TuShare API、输出路径、主键和特殊抓取方式。

## 字段生成

`tools/update_dataset_fields.py` 会解析 `docs/api_references/tushare/` 下的 TuShare API 参考资料，并生成：

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

## TuShare API 参考资料

| 项目 dataset | 文档 |
| --- | --- |
| `income` | [api_references/tushare/income.md](api_references/tushare/income.md) |
| `balancesheet` | [api_references/tushare/balancesheet.md](api_references/tushare/balancesheet.md) |
| `cashflow` | [api_references/tushare/cashflow.md](api_references/tushare/cashflow.md) |
| `forecast` | [api_references/tushare/forecast.md](api_references/tushare/forecast.md) |
| `express` | [api_references/tushare/express.md](api_references/tushare/express.md) |
| `dividend` | [api_references/tushare/dividend.md](api_references/tushare/dividend.md) |
| `fina_indicator` | [api_references/tushare/fina_indicator.md](api_references/tushare/fina_indicator.md) |
| `fina_audit` | [api_references/tushare/fina_audit.md](api_references/tushare/fina_audit.md) |
| `fina_mainbz` | [api_references/tushare/fina_mainbz.md](api_references/tushare/fina_mainbz.md) |
| `disclosure_date` | [api_references/tushare/disclosure_date.md](api_references/tushare/disclosure_date.md) |
