# CTI Adapter v0.4 Torch MLP Summary

Status: complete and pulled from Kaggle. This is a centralized neural stability/calibration probe, not a final federated result.

## Multi-seed Core Metrics

| cti_mode | accuracy_mean | accuracy_std | macro_f1_mean | macro_f1_std | fpr_normal_mean | fpr_normal_std | ece_mean | brier_mean | temp_ece_mean | temp_brier_mean | best_valid_macro_f1_mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| random_cti | 0.8637 | 0.0080 | 0.8168 | 0.0037 | 0.0134 | 0.0062 | 0.0168 | 0.1919 | 0.0168 | 0.1919 | 0.8189 |
| source_gate | 0.8590 | 0.0080 | 0.8175 | 0.0061 | 0.0338 | 0.0266 | 0.0198 | 0.1994 | 0.0180 | 0.1996 | 0.8200 |
| traffic_only | 0.8687 | 0.0106 | 0.8241 | 0.0119 | 0.0067 | 0.0013 | 0.0219 | 0.1871 | 0.0214 | 0.1870 | 0.8236 |
| weak_cti_concat | 0.8674 | 0.0020 | 0.8245 | 0.0007 | 0.0075 | 0.0015 | 0.0202 | 0.1880 | 0.0202 | 0.1880 | 0.8261 |

## Mean Delta vs Traffic-only

| cti_mode | delta_accuracy_vs_traffic | delta_macro_f1_vs_traffic | delta_fpr_normal_vs_traffic | delta_ece_vs_traffic | delta_brier_vs_traffic |
| --- | ---: | ---: | ---: | ---: | ---: |
| random_cti | -0.0050 | -0.0072 | +0.0067 | -0.0051 | +0.0048 |
| source_gate | -0.0097 | -0.0065 | +0.0271 | -0.0021 | +0.0123 |
| weak_cti_concat | -0.0013 | +0.0005 | +0.0008 | -0.0017 | +0.0009 |

## Interpretation

- The stable PyTorch centralized recipe works as a strong neural sanity baseline: traffic-only reaches mean Macro-F1 0.8241.
- Weak CTI concat is effectively tied with traffic-only on Macro-F1 (mean +0.0005) and does not justify a neural CTI improvement claim.
- Source gate underperforms traffic-only on mean Macro-F1 (-0.0066) and increases Normal FPR, so it remains an unfinished method component.
- Random CTI is below traffic-only on mean Macro-F1 (-0.0073), which preserves the negative-control logic.
- v0.4 should be used to justify the next neural baseline design, not to claim TrustFedFusion already improves neural IDS performance.

## Evidence Files

- Raw summary: `04_Results/metrics/kaggle_cti_v04_torch_mlp_summary.csv`
- Multi-seed table: `04_Results/tables/kaggle_cti_v04_torch_mlp_core_multiseed_summary.csv`
- Delta table: `04_Results/tables/kaggle_cti_v04_torch_mlp_deltas.csv`
- Per-family table: `04_Results/tables/kaggle_cti_v04_torch_mlp_per_family_summary.csv`
