# Code Included In This Release Candidate

Status: selected reproducibility scripts for internal release-candidate review. This is not yet a public software release.

## Included Scripts

| Path | Purpose | Execution boundary |
|---|---|---|
| `data_preparation/prepare_edge_iiot_ml_clean.py` | Build no-leakage Edge-IIoT ML processed CSVs and manifest | Requires original Edge-IIoT ML CSV supplied by the user/reviewer |
| `figures/plot_figure4.py` | Regenerate Figure 4 from the audited source CSV | Runs locally with `matplotlib` |
| `experiments/edge_matrix/run_experiment_matrix.py` | Edge-IIoT clean/robustness matrix entry script | Uses local or Kaggle-mounted processed Edge-IIoT clean CSV |
| `experiments/edge_matrix/train_baseline.py` | Baseline training logic used by the Edge matrix entry script | Helper for `run_experiment_matrix.py` |
| `experiments/ciciot_rare/train_ciciot_rare.py` | CICIoT2023 rare-family sampled probe | Intended for Kaggle-side mounted CICIoT2023 data |
| `experiments/unsw_baseline/train_unsw_baseline.py` | UNSW-NB15 official-split bounded baseline | Intended for Kaggle/local dataset files matching the script's search logic |
| `experiments/netflow_nearfull/train_netflow_nearfull_confirm.py` | NF-ToN/NF-BoT per-family-capped confirmation | Intended for Kaggle-side mounted NetFlow datasets |
| `experiments/cti_v08_posthoc_calibration/train_cti_v08_posthoc_calibration.py` | v0.8 post-hoc source-aware calibration boundary experiment | Intended for Kaggle/local UNSW-style files |

## Boundary Notes

- The scripts do not include credentials and should not require credentials inside the release package.
- Large third-party datasets are not redistributed here.
- Kaggle-oriented scripts use mounted input discovery and should be treated as reproducibility entry points, not as evidence that raw datasets are bundled.
- The current manuscript uses pulled result summaries under `results/tables/` as the evidence source.
- CTI v0.9 is intentionally not included as a completed experiment because it remains gated.

## Minimal Local Check

The Figure 4 script is the simplest local reproducibility check:

```bash
python code/figures/plot_figure4.py \
  --input figures/source_data/figure4_cross_dataset_data.csv \
  --output-prefix figures/final_assets/figure4_publication_draft
```

For dataset experiments, first obtain the original public datasets from their cited sources or mount them in a cloud notebook environment.
