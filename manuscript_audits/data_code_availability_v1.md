# Data and Code Availability Draft v1

Updated: 2026-06-16 02:00 +07

Status: internal draft for manuscript assembly. This is not final submission text because repository DOIs, public release links, and final code archive identifiers have not yet been created. Code and generated source-data/result licence decisions are now confirmed as MIT and CC BY 4.0, respectively.

## Data Availability

This study uses publicly available IoT/IIoT and network-intrusion datasets, together with processed no-leakage data tables, sampled cross-domain probes, result summaries, and figure source data generated during the analysis. The main processed Edge-IIoT table used for no-leakage experiments is retained locally in the project as `02_Data/processed/edge_iiot_ml_clean_full.csv`, with its processing manifest in `02_Data/processed/edge_iiot_ml_clean_manifest.json`. The quick reproducibility sample is retained as `02_Data/processed/edge_iiot_ml_clean_50001.csv`. These processed files remove the label-like `Attack_label` field and other leakage-prone or high-cardinality fields as described in the project manifest.

The original public datasets were obtained from their public dataset sources and are not redistributed as newly generated raw data by this study. Edge-IIoTset, CICIoT2023, UNSW-NB15, NF-ToN-IoT, and NF-BoT-IoT are treated as reused public or third-party public datasets, and the manuscript should cite their original dataset records or dataset papers where available. Large cross-domain datasets were accessed through Kaggle-side dataset mounts whenever possible; local storage keeps only clean, sample, schema, manifest, and result artifacts. This boundary is intentional and prevents bounded sampled or per-family-capped probes from being misrepresented as full raw-dataset final performance.

The source data underlying the manuscript tables and figures are retained in `04_Results/`, `04_Results/tables/`, and `05_Figures/`. Figure 4 source data are stored in `05_Figures/figure4_cross_dataset_data.csv`, with a row-level audit in `05_Figures/figure4_data_audit.md`, a generation script in `05_Figures/scripts/plot_figure4.py`, and draft assets in `05_Figures/figure4_publication_draft.svg`, `05_Figures/figure4_publication_draft.pdf`, and `05_Figures/figure4_publication_draft.png`. Result summaries for the main evidence blocks are stored as CSV, JSON, and Markdown files under `04_Results/`, including Edge-IIoT clean/CTI runs, CICIoT2023 sampled and rare-family probes, UNSW-NB15 bounded experiments, NetFlow stress and near-full per-family-capped confirmations, and v0.5-v0.8 calibration analyses.

No private production threat-intelligence feed, operational critical-infrastructure log, or sensitive human-subject dataset was used. The weak CTI-like evidence in this study is derived from observable protocol/source fields or controlled experimental hints and must not be described as production CTI. True target-label mappings such as `Attack_type -> TTP/family` are not used as model input.

Before submission, the figure source data, result summaries, manifests, and audit files should be deposited in a persistent repository such as Zenodo, Figshare, OSF, Dryad, or an institutional repository that issues a DOI. The final Data Availability statement should replace the local file paths above with the repository DOI/accession and should name exact source-data files for each figure and table. Raw third-party datasets and unverified processed full derivatives should remain excluded unless redistribution rights are verified.

## Code Availability

The code used for data preparation, experiment execution, result summarization, and figure generation is retained in the project workspace. The current reproducibility-relevant code includes the Edge-IIoT clean-data preparation script `03_Experiments/scripts/prepare_edge_iiot_ml_clean.py`, experiment plans and result notes under `03_Experiments/`, and the Figure 4 plotting script `05_Figures/scripts/plot_figure4.py`. The Figure 4 script has been run with the Python backend recorded in `05_Figures/figure4_generation_runbook.md`.

Before submission, the code package should be archived as a versioned public release in a repository such as Zenodo-linked GitHub, OSF, Software Heritage, or an institutional repository. The archived code record should include a README, environment file, execution order, data-source instructions, result-ingestion instructions for Kaggle outputs, and the exact commit or version used to generate the manuscript figures and tables. Cloud access tokens, personal credentials, and Kaggle/Colab authentication files must not be included in the code release. The selected code licence is MIT.

## Repository and Citation Actions

- Deposit source-data CSVs, result-summary tables, manifests, audit files, and figure source data in a persistent repository with DOI support under CC BY 4.0. Do not redistribute raw third-party datasets or unverified processed full derivatives.
- Deposit or archive reproducibility code with a stable release identifier.
- Cite original public datasets and dataset papers, including Edge-IIoTset and CICIoT2023, in the manuscript reference list.
- Add dataset citations for Kaggle-hosted third-party datasets where a stable dataset record or original publication exists.
- Add a README and file manifest mapping each public file to manuscript tables, figures, and experiment claims.

## Missing Information / Risk Flags

- Repository DOI/accession for the processed data package is not yet created.
- Repository DOI/accession for the code package is not yet created.
- Licences are selected: MIT for software code and CC BY 4.0 for generated result summaries, figure source data, manifests, and audit tables.
- Figure 4 draft assets are generated, but final journal-template scaling and any later source-data changes still require re-rendering and rechecking.
- P17 remains metadata-only and is unrelated to the data package, but its full-text status still controls the formal abstract boundary.
- Large third-party datasets should not be redistributed unless their licences permit redistribution.
- Kaggle dataset mounts are convenient for execution, but a manuscript data statement needs persistent identifiers or clear source citations rather than only local cloud paths.

## 中文核对

- 这份声明目前是投稿前草案，不是最终 Data Availability。
- 需要后续完成: 把结果表、图源数据、manifest 和审计文件上传到 Zenodo/Figshare/OSF/Dryad 或学校仓库，并生成 DOI。
- 需要后续完成: 代码仓库采用 GitHub+Zenodo 路线归档，并回填真实仓库 URL 和 DOI。
- 不能写“数据可向作者索取”作为主要方案，除非有明确限制原因和审核路径。
- 不能公开或保存任何 Kaggle/Colab token。
- 不能把 Kaggle 挂载路径当成长期可引用的数据 DOI。
