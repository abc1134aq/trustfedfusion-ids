# T1 数据集 Manifest

当前方法名: TrustFedFusion-IDS  
更新日期: 2026-06-15

## 已下载到本地的数据

| 优先级 | 数据集 | Kaggle ref | 本地路径 | 大小 | 标签列 | 用途 |
| --- | --- | --- | --- | ---: | --- | --- |
| P0 | Edge-IIoT Balanced Subset | `kavyasriyamani/edge-iiot-balanced-subset-for-intrusion-detection` | `02_Data/kaggle/edge_iiot_balanced/edge_iiot.csv` | 6.1 MB | `Attack_Label` | 本地 smoke test、快速验证 FedAvg/FedProx |
| P0 | Edge-IIoT ML version | `sibasispradhan/edge-iiotset-dataset` | `02_Data/kaggle/edge_iiot_ml/ML-EdgeIIoT-dataset.csv` | 82 MB CSV | `Attack_type` | 第一阶段主实验，15 类攻击 |
| P1 | CICIoT2023 small | `onmnhc/ciciot2023` | `02_Data/kaggle/ciciot2023_small/Merged01.csv` | 140 MB | `Label` | 第二阶段跨域/未知攻击验证 |
| P1 | UNSW-NB15 | `dhoogla/unswnb15` | `02_Data/kaggle/unsw_nb15/*.parquet` | 14 MB | 待 parquet 读取 | 跨域传统 NIDS 数据 |
| P1 | NF-ToN-IoT | `dhoogla/nftoniot` | `02_Data/kaggle/nf_ton_iot/*.parquet` | 9.1 MB | 待 parquet 读取 | ToN-IoT 跨域 |
| P1 | NF-BoT-IoT | `dhoogla/nfbotiot` | `02_Data/kaggle/nf_bot_iot/*.parquet` | 2.2 MB | 待 parquet 读取 | Bot-IoT 跨域 |

## 已处理数据

| 数据 | 本地路径 | 大小 | 标签列 | 处理规则 | 用途 |
| --- | --- | ---: | --- | --- | --- |
| Edge-IIoT ML clean full | `02_Data/processed/edge_iiot_ml_clean_full.csv` | 38 MB | `Attack_type` | 删除高基数时间/IP/payload字段；排除 `Attack_label` 标签泄漏列 | Kaggle 主实验、无泄漏本地 full baseline |
| Edge-IIoT ML clean sample | `02_Data/processed/edge_iiot_ml_clean_50001.csv` | 12 MB | `Attack_type` | 按类别比例抽样；同样排除标签泄漏列 | Kaggle 失败时的备用轻量包 |

处理清单:

- `02_Data/processed/edge_iiot_ml_clean_manifest.json`
- `03_Experiments/scripts/prepare_edge_iiot_ml_clean.py`

## Kaggle 完整训练推荐

| 任务 | 推荐数据源 | 原因 |
| --- | --- | --- |
| 第一阶段主实验 | 本地 clean CSV 或 `sibasispradhan/edge-iiotset-dataset` | 优先用 clean CSV，避免 Kaggle 读取原始大 CSV 崩溃和标签泄漏 |
| 数据集原始复核 | `mohamedamineferrag/edgeiiotset-cyber-security-dataset-of-iot-iiot` | 原始 Edge-IIoTset 更完整，但体积大，适合 Kaggle/云端挂载 |
| 跨域扩展 | `riddymazumder/ciciot2023` 或 `madhavmalhotra/unb-cic-iot-dataset` | 已通过 Kaggle CLI 核实可检索，full 约 1.5GB-3GB，适合 Kaggle 挂载而不是本地长期保存 |
| 低成本跨域 | `dhoogla/nfunswnb15v2`, `dhoogla/nftoniot`, `dhoogla/nfbotiotv2` | NetFlow 统一格式，后续适合做跨数据集统一特征 |

## 当前实验选择

1. 本地 smoke test: `edge_iiot_balanced`。
2. 本地/云端第一主实验: `edge_iiot_ml`。
3. Kaggle 第二主实验: `edge_iiot_ml + ciciot2023`。
4. 跨域第三阶段: NF-UNSW-NB15 / NF-ToN-IoT / NF-BoT-IoT 统一 NetFlow 特征。

## 注意

- Parquet 数据本地需要 `pyarrow` 或 `fastparquet`；Kaggle 通常可直接读。
- 小样本高分不能作为论文结论，只能证明管线可跑。
- 正式论文必须报告非 IID、跨域、投毒/后门、通信量和推理延迟。
- 数据存放策略见: `02_Data/manifests/data_storage_strategy.md`。大数据集优先挂 Kaggle，本地只保留 clean/sample/manifest。
- 当前决策: 不把 full CICIoT2023 下载到本地；下一步在 Kaggle kernel 内做 schema/sample probe，再决定跨域实验子集。
