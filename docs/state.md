# 状态与失败清单

## 下载状态

`funda download` 默认使用 `auto` 状态后端。新数据目录会使用 SQLite 状态库：

```text
data/_state/state.db
```

显式使用 JSON：

```text
funda download --state-backend json
```

可用 `--state-path` 覆盖路径：

```bash
funda download --state-path data/_state/custom_state.db
funda download --state-backend json --state-path data/_state/state.json
```

`auto` 模式规则：

- 指定 `--state-path *.db` 时使用 SQLite。
- 指定其他 `--state-path` 时使用 JSON。
- 未指定路径且 `<data_dir>/_state/state.db` 已存在时使用 SQLite。
- 未指定路径且只存在旧 `<data_dir>/_state/state.json` 时复制迁移到 SQLite。
- 新数据目录默认使用 `<data_dir>/_state/state.db`。

状态文件记录每个数据集的增量游标。删除状态文件或换一个 `state_path` 会让下载计划重新计算，但已经存在的 parquet 分区仍会参与合并和去重。

## 失败清单

失败记录写入：

```text
<data_dir>/_state/failures/
```

常见文件名：

```text
income_periods.json
fina_audit_per_stock.json
dividend_windows.json
```

查看失败清单：

```bash
funda state ls-failures --data-dir data
```

失败清单包含数据集、失败类型、生成时间和失败窗口或报告期。下一次下载会继续按状态和刷新窗口补抓；如需强制扩大补抓范围，可调整 `--since`、`--quarters` 或删除对应状态。

## 查看和维护状态

查看全部 JSON 状态：

```bash
funda state show --backend json --data-dir data
```

查看默认 SQLite 状态：

```bash
funda state show --state-backend sqlite --data-dir data
```

查看单个数据集：

```bash
funda state show --backend json --data-dir data --dataset income
```

设置状态键：

```bash
funda state set --backend json --data-dir data \
  --dataset income --key last_period --value 20231231
```

清理状态：

```bash
funda state clear --backend json --data-dir data --dataset income
funda state clear --backend json --data-dir data --dataset income --key last_period
```

## SQLite 状态后端

SQLite 后端用于查看和维护 `kv_state`、`watermarks`、`dataset_state` 和 `run_log` 等状态表。

```bash
funda state show --backend sqlite --state-path data/_state/state.db
funda state set --backend sqlite --state-path data/_state/state.db \
  --dataset income --key last_period --value 20231231
```

`funda download` 和 `funda state` 使用同一套后端解析规则。旧 JSON 状态迁移到 SQLite 时，原始 `state.json` 会保留在磁盘上，便于回退和人工核对。
