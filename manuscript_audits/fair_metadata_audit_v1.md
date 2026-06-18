# FAIR Metadata Audit v1

Updated: 2026-06-16 02:00 +07

Status: pre-repository FAIR audit for the TrustFedFusion-IDS reproducibility package.

## Quick FAIR Assessment

| Principle | Current status | Gap | Action |
|---|---|---|---|
| Findable | Local manifests and tables exist | No public DOI/accession yet | Deposit release package in DOI-supporting repository |
| Accessible | Local files are organized; public datasets have source records | Local paths are not durable public access routes | Replace local paths with repository DOI and public dataset citations |
| Interoperable | CSV/JSON/Markdown dominate; parquet used for some third-party samples | Need data dictionary and column definitions in public package | Add README and variable dictionary |
| Reusable | Processing manifests and audits exist | Licence, version, checksums, and clean release structure missing | Add licence, release version, and file manifest |

## Dataset and Artifact Inventory

| Artifact family | Current local evidence | Access route classification | Repository action |
|---|---|---|---|
| Edge-IIoT processed no-leakage CSV | `02_Data/processed/edge_iiot_ml_clean_full.csv` | Generated processed data | Deposit if redistribution rights allow; otherwise deposit script + manifest and cite original |
| Edge-IIoT clean sample | `02_Data/processed/edge_iiot_ml_clean_50001.csv` | Generated processed data / sample | Deposit as reproducibility sample if permitted |
| Edge-IIoT processing manifest | `02_Data/processed/edge_iiot_ml_clean_manifest.json` | Within repository/supplement | Deposit |
| Dataset manifests | `02_Data/manifests/*.md` | Within repository/supplement | Deposit |
| Result summaries | `04_Results/tables/*.md`, `04_Results/tables/*.csv` | Generated source data | Deposit |
| Per-family outputs | selected `04_Results/**/**per_family.csv` | Generated source data | Deposit selected files or a compressed archive |
| Figure source data | `05_Figures/figure4_cross_dataset_data.csv` | Figure source data | Deposit |
| Figure final assets | Figures 1/2/3/4/5 draft assets exist | Figure source/final data | Deposit after final journal-template QA |
| Experiment code | `03_Experiments/`, `07_Colab_Ready/` | Code | Archive release after cleanup |
| Public raw datasets | Edge-IIoTset, CICIoT2023, UNSW-NB15, NF-ToN, NF-BoT | Reused public / third-party public source | Cite original records; do not blindly redistribute full raw datasets |

## DataCite-Style Metadata Needed

| Field | Current value / action |
|---|---|
| Identifier | Missing; repository DOI needed |
| Creator | Confirm author list before deposit |
| Title | Suggested: `TrustFedFusion-IDS reproducibility package: processed data, source data, and result summaries` |
| Publisher / repository | Choose Zenodo/Figshare/OSF/Dryad/institutional repository |
| Publication year | 2026 if deposited this year |
| Resource type | Dataset and software, or two separate records |
| Version | Suggested first release: `v0.1-preprint` or `v1.0-submission` after final audit |
| Licence | Missing; choose data and code licences separately |
| Related identifiers | Add manuscript DOI/preprint later; add code/data cross-links |
| Description | Must mention processed no-leakage Edge-IIoT data, result summaries, figure source data, and Kaggle-first boundaries |

## README/Data Dictionary Requirements

The deposit README must include:

- file list and sizes;
- source dataset names and original citations;
- processing steps that remove leakage-prone fields;
- target labels used in each dataset;
- variant names: `traffic_only`, `weak_cti_concat`, `source_gate`, `random_cti`, calibration variants;
- metric definitions: Accuracy, Macro-F1, Normal FPR, ECE, Brier score, mean confidence;
- missing-value handling and blank fields in Figure 4 CSV;
- exact command used for Figure 4 generation with the Python backend;
- explanation that bounded probes are not full raw-dataset final performance.

## Blocking Issues Before Submission

| Issue | Severity | Fix |
|---|---|---|
| No public DOI/accession for processed data/results | Major | Create repository deposit before submission or provide reviewer-accessible private link |
| No public code archive DOI | Major | Create versioned code release |
| Figure 4 final assets need final-template recheck | Minor/Major depending on later changes | Re-render only if source CSV or final template changes; keep QA with release |
| Licence choices missing | Major | Select data/code licences compatible with third-party dataset terms |
| Full raw third-party redistribution unclear | Major | Cite original sources and avoid redistributing full raw datasets unless permitted |
| P17 full text missing | Manuscript gate, not data gate | Keep P17 metadata-only |

## Recommended Repository Strategy

Preferred minimal strategy:

1. Create one dataset/source-data repository record for processed data, result summaries, figure source data, manifests, and final figure assets.
2. Create one software repository release for scripts and runbooks.
3. Cross-link the two records.
4. Cite original public datasets separately.

Alternative compact strategy:

1. One combined Zenodo/OSF record containing `data/`, `results/`, `figures/`, and `code/`.
2. Use a clear README to separate data and code licences.

## Chinese Author Notes

- “数据可向作者索取”不够强，除非有明确限制和审核路径。
- Kaggle 路径方便实验，但不是投稿时最稳的数据 DOI。
- 处理后数据如果受原始数据许可限制，至少应公开处理脚本、manifest、结果表和 Figure source data。
- Figure source data 是投稿审查重点，不能只放图片。
