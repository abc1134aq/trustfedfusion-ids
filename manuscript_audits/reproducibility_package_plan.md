# Reproducibility Package Plan

Updated: 2026-06-16 02:00 +07

Status: pre-submission reproducibility plan. This file defines what must be packaged before formal submission. It does not claim that a public repository release already exists.

## Package Goals

The reproducibility package should allow a reviewer or future reader to inspect the evidence chain behind TrustFedFusion-IDS without requiring access to the author's local machine, private cloud credentials, or large duplicated raw datasets.

## Package Contents

| Package component | Include | Current local source | Release status |
|---|---|---|---|
| Processed no-leakage Edge-IIoT data | `edge_iiot_ml_clean_full.csv`, sample CSV, manifest | `02_Data/processed/` | Local only; needs repository DOI |
| Dataset manifests | data storage strategy, dataset manifest, CTI mapping manifest | `02_Data/manifests/` | Local only |
| Result summaries | cross-dataset matrix, Table 3 source data, per-experiment summaries | `04_Results/tables/`, selected `04_Results/*summary*` | Local only |
| Figure source data | Figure 4 CSV, figure audits, plotting script, draft SVG/PDF/PNG assets | `05_Figures/` | Local draft ready; needs final-template QA and repository DOI |
| Experiment code | data prep script, reproducible experiment scripts or exported kernels | `03_Experiments/scripts/`, `07_Colab_Ready/` | Needs cleanup and token scan |
| Runbooks | cloud result ingestion, Figure 4 generation, calibration decision | `09_Project_Management/`, `05_Figures/` | Local only |
| Manuscript evidence gates | claim registry, Tables 1-4, audits | `06_Manuscript/` | Local only |

## Exclusions

Do not include:

- Kaggle/Colab tokens or authentication files.
- Local OAuth files.
- User-specific SSH keys or cloud credentials.
- Large raw public datasets if licence or storage policy does not permit redistribution.
- HTML challenge pages or failed PDF downloads.
- Smoke-test outputs presented as manuscript evidence.

## Recommended Public Release Structure

```text
trustfedfusion-ids-reproducibility/
  README.md
  data/
    processed/
    manifests/
  results/
    tables/
    selected_per_family/
  figures/
    source_data/
    final_assets/
  code/
    data_preparation/
    experiments/
    figures/
  runbooks/
  environment/
  LICENSE
  CITATION.cff
```

## README Requirements

The public README should state:

1. What the package reproduces.
2. Which datasets are reused public datasets.
3. Where full large datasets can be obtained.
4. Which local files are processed derivatives or result summaries.
5. How to run the clean-data preparation script.
6. How to regenerate Figure 4.
7. Which experiments were run on Kaggle and how outputs were ingested.
8. Which claims are partial or bounded.
9. What is intentionally not included.

## Environment Requirements

Current known local requirements:

- Python 3.
- `pandas`, `numpy`, `scikit-learn` for data/results.
- `matplotlib` for Figure 4.
- Optional: `pyarrow` or `fastparquet` for parquet datasets.

Note: the system Python lacks `matplotlib`; Figure 4 generation currently uses bundled Codex Python:

```bash
python
```

The public package should provide a portable `requirements.txt` or `environment.yml` rather than relying on this local path.

## Claim-to-Artifact Mapping

| Claim family | Required artifact |
|---|---|
| No-leakage Edge experiments | clean CSV, manifest, preparation script, Edge result summaries |
| Weak/source evidence signal | CTI result summaries, Table 3, Figure 4 source data |
| Random CTI control | random CTI result JSON/CSV summaries |
| Robust aggregation failure | robustness matrix summaries |
| Cross-domain bounded evidence | CICIoT/UNSW/NetFlow summaries and manifests |
| Calibration unresolved | v0.5-v0.8 calibration summaries |
| Figure 4 | CSV, script, final SVG/PDF/PNG, QA note |

## Release Gates

Before public release:

1. Run token scan.
2. Remove `.DS_Store` and local-only transient files.
3. Confirm all included data can be redistributed.
4. Add licence choices for data and code.
5. Add checksums or repository-generated file hashes.
6. Generate a DOI/accession.
7. Update `data_code_availability_v1.md` with final repository identifiers.

## Current Status

The package is not ready for public deposit yet. The next concrete step is to finish Figure 4 and then assemble a clean release candidate directory without credentials, transient files, or unsupported claims.
