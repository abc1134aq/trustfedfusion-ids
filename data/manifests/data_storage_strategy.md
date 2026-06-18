# 数据存放策略

更新日期: 2026-06-15

## 当前结论

实验环境以 Kaggle 为主，本地只保留可复现所必需的数据、clean 小版本和 manifest。原因:

- 当前本机空间充足: 工作区约 427MB，本机剩余约 694GB。
- 但后续完整 CICIoT2023、原始 Edge-IIoTset、多个 NetFlow 数据集可能快速增长到数 GB 以上。
- Kaggle 实验直接挂 Kaggle dataset，能避免重复上传和本地磁盘膨胀。

## 2026-06-15 核实结论

- 本地不是当前瓶颈: 本轮核实工作区约 489MB，`02_Data` 约 313MB，本机可用空间约 691GB。
- 但不应该把 full CICIoT2023/原始 Edge-IIoTset/多份 NetFlow 全量长期堆在本地；实验环境以 Kaggle 为准，避免本地与云端重复存储。
- 已确认 Kaggle 上可直接挂载 CICIoT2023 数据集，例如 `riddymazumder/ciciot2023` 约 1.5GB、`madhavmalhotra/unb-cic-iot-dataset` 约 3GB。
- 第一阶段可使用用户自行创建的 Kaggle dataset，例如 `<kaggle-user>/edge-iiot-ml-clean-trustfedfusion`，或使用本 release 中允许公开的处理脚本与 manifest 重新生成。
- 本地只保留无泄漏 clean CSV、sample、manifest 和必要小版本，便于 smoke test 与审稿复现说明。
- 当前保留的主实验数据为 `edge_iiot_ml_clean_full.csv` 157,800 行 / 38MB，以及 `edge_iiot_ml_clean_50001.csv` 50,001 行 / 12MB。

## 放 Kaggle 的数据

| 数据 | 策略 | 说明 |
| --- | --- | --- |
| Edge-IIoT ML clean full | Kaggle + 本地保留一份 | 当前主实验数据；公开复现时可由用户自行上传到 Kaggle dataset 或按脚本本地生成 |
| Edge-IIoT 原始完整数据 | Kaggle 优先 | 原始数据体积大，本地不主动扩展下载 |
| CICIoT2023 full | Kaggle 优先 | 本地已有 small CSV；full 只在 Kaggle 使用 |
| CICIoT2023 Kaggle candidates | Kaggle 直接挂载 | `riddymazumder/ciciot2023`、`madhavmalhotra/unb-cic-iot-dataset` |
| NF-ToN / NF-BoT / UNSW parquet | Kaggle 优先 + 本地小版本 | 本地保留小 parquet 用于 schema 检查 |

## 本地必须保留的数据

| 文件 | 用途 |
| --- | --- |
| `02_Data/processed/edge_iiot_ml_clean_full.csv` | 无泄漏主实验可复现 |
| `02_Data/processed/edge_iiot_ml_clean_50001.csv` | Kaggle/Colab 快速测试 |
| `02_Data/processed/edge_iiot_ml_clean_manifest.json` | 数据清洗可追溯 |
| `02_Data/manifests/*.md` | 数据来源、标签、CTI 映射记录 |

## 不再本地扩张的规则

- 不主动下载超过 1GB 的原始数据到本地，除非明确需要离线清洗。
- 大数据集优先用 Kaggle dataset source。
- 本地只保存 processed/clean/sample 版本和读取脚本。
- 每次新增数据必须更新 `02_Data/manifests/dataset_manifest.md`。
