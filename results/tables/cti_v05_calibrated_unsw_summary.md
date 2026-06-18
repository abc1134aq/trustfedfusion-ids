# CTI v0.5 Calibrated UNSW Summary

Status: complete locally using the local UNSW parquet copies. Kaggle submission is pending because the current account hit the batch CPU session limit.

## Multi-seed Core Metrics

| scenario | accuracy_mean | macro_f1_mean | macro_f1_std | normal_fpr_mean | raw_ece_mean | temp_ece_mean | raw_brier_mean | temp_brier_mean | temperature_mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| random_cti | 0.4720 | 0.2261 | 0.0009 | 0.5529 | 0.0749 | 0.0511 | 0.6855 | 0.6817 | 0.8000 |
| source_gate | 0.5459 | 0.2974 | 0.0035 | 0.4921 | 0.1061 | 0.1061 | 0.5528 | 0.5528 | 1.0000 |
| source_gate_pruned | 0.5308 | 0.2815 | 0.0114 | 0.4898 | 0.1184 | 0.1184 | 0.5578 | 0.5578 | 1.0000 |
| traffic_only | 0.4675 | 0.2161 | 0.0013 | 0.5559 | 0.0704 | 0.0506 | 0.6858 | 0.6819 | 0.8000 |
| weak_cti_concat | 0.5119 | 0.2690 | 0.0084 | 0.5394 | 0.1213 | 0.1133 | 0.5853 | 0.5838 | 0.9000 |

## Mean Delta vs Traffic-only

| scenario | delta_macro_f1_vs_traffic | delta_normal_fpr_vs_traffic | delta_raw_ece_vs_traffic | delta_temp_ece_vs_traffic | temp_ece_improvement_vs_raw | temp_brier_improvement_vs_raw |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| random_cti | +0.0101 | -0.0030 | +0.0044 | +0.0005 | -0.0238 | -0.0038 |
| source_gate | +0.0813 | -0.0638 | +0.0357 | +0.0556 | +0.0000 | +0.0000 |
| source_gate_pruned | +0.0654 | -0.0661 | +0.0479 | +0.0678 | +0.0000 | +0.0000 |
| weak_cti_concat | +0.0530 | -0.0165 | +0.0508 | +0.0628 | -0.0079 | -0.0014 |

## Interpretation

- Source gate remains the strongest v0.5 UNSW setting on Macro-F1: mean 0.2974 versus traffic-only 0.2161 and weak CTI 0.2690.
- Source gate lowers Normal FPR versus traffic-only by mean -0.0180, but this FPR gain is smaller than in the previous no-validation UNSW run.
- Temperature scaling improves traffic-only and random CTI ECE, slightly improves weak CTI ECE, but does not improve source gate or pruned source gate because selected temperature stays 1.0.
- Pruning raw CTI hints does not solve calibration; it lowers Macro-F1 relative to full source gate and keeps ECE high.
- v0.5 therefore answers the calibration question honestly: source gate performance is promising, but a simple post-hoc temperature/pruning fix is insufficient for a calibrated source-gate method.

## Evidence Files

- Result directory: `04_Results/cti_v05_calibrated_unsw/`
- Multi-seed table: `04_Results/tables/cti_v05_calibrated_unsw_multiseed_summary.csv`
- Delta table: `04_Results/tables/cti_v05_calibrated_unsw_deltas.csv`
