# TrustFedFusion-IDS reproducibility package

Status: repository identifiers applied. Code repository: https://github.com/abc1134aq/trustfedfusion-ids; Code DOI/accession: 10.5281/zenodo.20748694; source-data/results repository: https://zenodo.org/records/20748765; source-data/results DOI/accession: 10.5281/zenodo.20748765; publication date: 2026-06-18.

## What this package supports

This package supports the manuscript:

TrustFedFusion-IDS: Reliability-Aware Federated Threat-Intelligence Fusion for Cross-Domain Intrusion Detection in Critical Infrastructure

It provides the processed data, result summaries, source data, figure-generation code, and runbooks needed to inspect the manuscript's evidence chain. The package is designed to reproduce the reported source-data tables and figures, not to redistribute all raw third-party datasets.

## Important boundaries

- The package does not include Kaggle, Colab, SSH, OAuth, or other credentials.
- Large raw third-party datasets are not redistributed unless their licences permit redistribution.
- CICIoT2023 and NetFlow results are bounded sampled, stress, official-split, or per-family-capped evidence where stated in the manuscript.
- Weak CTI-like evidence is derived from observable protocol/source fields or controlled experimental hints. It is not a production CTI feed.
- True target-label mappings such as `Attack_type -> TTP/family` are not used as model input.
- Calibration is reported as unresolved through v0.8.
- P17/FedKD-IDS remains metadata-only until a legal full text or author manuscript is available.

## Package layout

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
    README.md
  runbooks/
  environment/
  LICENSE
  SOURCE_DATA_LICENSE.md
  CITATION.cff
```

## Reused public datasets

The study reuses public IoT/IIoT and network-intrusion datasets. Cite the original dataset records or dataset papers in any reuse:

| Dataset | Role | Local release strategy |
|---|---|---|
| Edge-IIoTset / Edge-IIoT ML version | Main no-leakage Edge/IIoT experiments | Include processed no-leakage derivative if redistribution terms permit; always include preparation script and manifest |
| CICIoT2023 | Cross-domain sampled and rare-family probes | Cite original source; do not treat sampled runs as full CICIoT final performance |
| UNSW-NB15 | Official-split cross-domain bounded experiments | Cite original source; include result summaries |
| NF-ToN-IoT | NetFlow stress and per-family-capped confirmation | Cite original source; include result summaries |
| NF-BoT-IoT | NetFlow stress and per-family-capped confirmation | Cite original source; include result summaries |

## Processed data boundary

The main processed Edge-IIoT file removes leakage-prone fields, including the label-like `Attack_label` column. The processing manifest records the provenance and cleaning rules.

The current public release candidate prioritizes preparation code, manifests, result summaries, and figure source data. If redistribution terms permit a processed Edge-IIoT derivative in the final public record, expected files would be:

```text
data/processed/edge_iiot_ml_clean_full.csv
data/processed/edge_iiot_ml_clean_50001.csv
data/processed/edge_iiot_ml_clean_manifest.json
data/manifests/
```

If processed data cannot be redistributed under the original dataset terms, release the preparation script, manifest, result summaries, and figure source data instead, and direct users to the original public dataset source.

## Reproducing processed Edge-IIoT data

Run the preparation script from a workspace that contains the original Edge-IIoT ML CSV:

```bash
python code/data_preparation/prepare_edge_iiot_ml_clean.py
```

The public code release should document the expected input path, output path, and excluded columns. The manuscript evidence requires that `Attack_label` is not used as a feature.

## Experiment scripts

Selected reproducibility entry points are included under:

```text
code/experiments/
```

These scripts cover the Edge matrix, CICIoT rare-family probe, UNSW bounded baseline, NetFlow near-full confirmation, and v0.8 post-hoc calibration boundary experiment. They are included as traceable experiment entry points, not as a claim that full raw third-party datasets are bundled. See `code/README.md` for script-specific boundaries.

## Inspecting result evidence

Result summaries are organized under:

```text
results/tables/
results/selected_per_family/
```

Use these files to inspect:

- Edge-IIoT clean and CTI v0-v0.4 evidence.
- CICIoT2023 sampled and rare-family evidence.
- UNSW-NB15 v0.5-v0.8 calibration evidence.
- NF-ToN/NF-BoT stress and per-family-capped evidence.
- Cross-dataset positive, neutral, and negative evidence.

The manuscript claim gate is Table 4. Do not promote a result claim unless it is backed by a result summary and the claim registry.

## Regenerating Figure 4

Figure 4 uses:

```text
figures/source_data/figure4_cross_dataset_data.csv
code/figures/plot_figure4.py
```

After installing the release environment:

```bash
python code/figures/plot_figure4.py \
  --input figures/source_data/figure4_cross_dataset_data.csv \
  --output-prefix figures/final_assets/figure4_publication_draft
```

Expected outputs:

```text
figures/final_assets/figure4_publication_draft.svg
figures/final_assets/figure4_publication_draft.pdf
figures/final_assets/figure4_publication_draft.png
```

The final plot must show positive, neutral, and negative evidence. It must not imply that source gating is universally best or that calibration is solved.

## Environment

Install the release dependencies:

```bash
python -m pip install -r environment/requirements.txt
```

Core dependencies:

- `numpy`
- `pandas`
- `scikit-learn`
- `matplotlib`
- `pyarrow` for parquet input where needed
- `torch` for neural baseline scripts where included

## Cloud-result ingestion

Some experiments were run on Kaggle because large cross-domain datasets are best accessed through Kaggle-side mounts. The release package includes runbooks and pulled result summaries, not cloud credentials.

Cloud outputs become manuscript evidence only after:

1. outputs are pulled locally;
2. summaries are generated under `results/`;
3. source data are mapped to tables or figures;
4. the claim registry is updated;
5. token and high-risk wording scans pass.

## What is not included

- Cloud credentials or API tokens.
- Full raw third-party datasets when redistribution rights are unclear.
- Failed PDF downloads or HTML challenge pages.
- Smoke-test outputs used only for debugging.
- Claims about P17/FedKD-IDS that require full-text access.

## Citation

For public citation, cite the code record and source-data/results record using these persistent identifiers: code repository https://github.com/abc1134aq/trustfedfusion-ids, code DOI/accession 10.5281/zenodo.20748694; source-data/results repository https://zenodo.org/records/20748765, source-data/results DOI/accession 10.5281/zenodo.20748765.

## Licence

The software code in this release candidate is prepared under the MIT License. Generated result summaries, figure source data, manifests, and audit tables are prepared under CC BY 4.0, subject to final repository policy checks. Raw third-party cybersecurity datasets, publisher PDFs, cloud credentials, and unverified processed full derivatives are excluded from the public release package.
