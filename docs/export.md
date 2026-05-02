# 导出说明

`funda download` 默认只写 parquet 缓存。需要生成 CSV 或整理后的 parquet 文件时，运行：

```bash
funda export --dataset-root data --out-dir data/export
```

默认行为：

- 读取 `--dataset-root`，默认 `data`。
- 输出格式为 CSV。
- 自动扫描可导出的平面数据集。
- `--kinds` 默认为空，因此默认跳过 `income` 派生口径。
- 输出目录为 `<out-dir>/csv/`；如果 `--out-dir` 本身名为 `csv`，则直接写入该目录。

## 平面导出

平面导出会把每个数据集的 parquet 分区合并为一个文件：

```bash
funda export --dataset-root data --out-dir data/export
```

指定数据集：

```bash
funda export --flat-datasets balancesheet,cashflow
```

排除数据集：

```bash
funda export --flat-exclude dividend,fina_audit
```

跳过平面导出：

```bash
funda export --no-flat --kinds annual,single,cumulative
```

按年度分区拆成多个文件：

```bash
funda export --flat-datasets balancesheet --split-by year
```

## `income` 派生口径

`income` 下载结果是季度累计值。导出时可生成：

| 口径 | 说明 |
| --- | --- |
| `cumulative` | 季度累计值 |
| `single` | 由累计值差分得到单季值 |
| `annual` | 年度值 |

示例：

```bash
funda export --kinds annual,single,cumulative \
  --annual-strategy cumulative \
  --dataset-root data \
  --out-format csv \
  --out-dir data/export
```

年度策略：

- `cumulative`：使用 12-31 期末的累计值。
- `sum4`：将四个单季值相加。

只导出 `income` 派生口径：

```bash
funda export --kinds annual,single,cumulative --no-flat
```

跳过 `income` 派生口径：

```bash
funda export --no-income
```

## 格式和压缩

导出 parquet：

```bash
funda export --out-format parquet --out-dir data/export
```

CSV gzip 压缩：

```bash
funda export --out-format csv --gzip --out-dir data/export
```

`--gzip` 只支持 CSV。

## 下载后自动导出

```bash
funda download --export --export-kinds annual,single,cumulative
```

下载命令中的导出相关参数：

| 参数 | 说明 |
| --- | --- |
| `--export` | 下载完成后执行导出 |
| `--no-export` | 显式关闭自动导出 |
| `--export-format csv|parquet` | 导出格式 |
| `--export-out-dir DIR` | 导出目录 |
| `--export-kinds annual,single,cumulative` | `income` 派生口径 |
| `--export-annual-strategy cumulative|sum4` | 年度策略 |
| `--export-years N` | 导出最近 N 年 |
| `--strict-export` | 导出失败时返回错误 |

自动导出也支持配置文件中的 `export_flat_datasets`、`export_flat_exclude`、`export_split_by`、`export_gzip`、`export_no_income` 和 `export_no_flat`。
