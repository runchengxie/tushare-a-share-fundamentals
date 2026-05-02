# 文档索引

本目录保存项目使用文档和 TuShare API 字段参考。

## 项目文档

- [usage.md](usage.md)：下载流程、数据集选择、进度展示、覆盖率检查和旧版目录说明。
- [configuration.md](configuration.md)：`config.yml`、环境变量、token、VIP 检测和导出配置。
- [datasets.md](datasets.md)：数据集、TuShare API、抓取粒度、主键、去重键和报表类型。
- [export.md](export.md)：平面导出、`income` 派生导出、压缩、按年拆分和自动导出。
- [state.md](state.md)：下载状态、失败清单、JSON 后端和 SQLite 维护后端。
- [development.md](development.md)：测试、代码检查、字段生成和维护脚本。

## TuShare API 参考资料

`docs/api_references/tushare/` 保存外部接口字段表，供字段生成脚本读取。修改这些文件后，应重新生成：

```bash
uv run tools/update_dataset_fields.py
```

只检查解析结果：

```bash
uv run tools/update_dataset_fields.py --check
```

| 项目数据集 | 本地字段参考 |
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

## 维护脚本

- `tools/update_dataset_fields.py`：从 TuShare 字段参考生成 `src/tushare_a_fundamentals/meta/doc_fields.py`。
- `project_tools/verify_tushare_tokens.py`：检查一个或多个 TuShare token 的积分和 VIP 可用性。
- `project_tools/check_api_availability.py`：诊断单个 TuShare API 的权限、字段和返回结果。
- `project_tools/export_repo_source.py`：导出源码快照，便于离线审阅。
- `project_tools/package.sh`：维护者打包辅助脚本。
