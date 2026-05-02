# 状态与失败清单

## 下载状态

`funda download` 目前使用 JSON 状态文件。默认路径：

```text
data/_state/state.json
```

可用 `--state-path` 覆盖：

```bash
funda download --state-path data/_state/custom_state.json
```

`--state-path` 在下载流程中只表示 JSON 文件路径。后缀不会自动切换后端；请避免把下载状态写到 `.db` 路径。

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

## SQLite 维护后端

`funda state` 支持 SQLite 后端，用于查看和维护 `kv_state`、`watermarks`、`dataset_state` 等状态表。

```bash
funda state show --backend sqlite --state-path meta/state.db
funda state set --backend sqlite --state-path meta/state.db \
  --dataset income --key last_period --value 20231231
```

`--backend auto` 的规则只适用于 `funda state`：

- 指定 `--state-path *.db` 时使用 SQLite。
- 指定其他 `--state-path` 时使用 JSON。
- 未指定路径且仓库根目录存在 `meta/state.db` 时使用 SQLite。
- 其他情况使用 `<data_dir>/_state/state.json`。

SQLite 后端当前不参与 `funda download` 的增量写入。
