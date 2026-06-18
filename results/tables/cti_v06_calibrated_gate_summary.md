# CTI v0.6 Calibrated Gate Summary

Status: complete on Kaggle and pulled locally.

## Multi-seed Core Metrics

| scenario | alpha_mean | accuracy_mean | macro_f1_mean | macro_f1_std | normal_fpr_mean | raw_ece_mean | temp_ece_mean | raw_brier_mean | temp_brier_mean | temp_mean_confidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| traffic_only | 1.0000 | 0.4675 | 0.2161 | 0.0013 | 0.5559 | 0.0704 | 0.0506 | 0.6858 | 0.6819 | 0.4454 |
| weak_cti_concat | 1.0000 | 0.5119 | 0.2690 | 0.0084 | 0.5394 | 0.1213 | 0.1133 | 0.5853 | 0.5838 | 0.5529 |
| source_gate | 1.0000 | 0.5459 | 0.2974 | 0.0035 | 0.4921 | 0.1061 | 0.1061 | 0.5528 | 0.5528 | 0.5856 |
| cal_source_gate | 1.2500 | 0.5513 | 0.3029 | 0.0120 | 0.4863 | 0.1119 | 0.1084 | 0.5491 | 0.5527 | 0.6036 |
| random_cti | 1.0000 | 0.4720 | 0.2261 | 0.0009 | 0.5529 | 0.0749 | 0.0511 | 0.6855 | 0.6817 | 0.4462 |
| cal_random_source_gate | 0.4167 | 0.4724 | 0.2236 | 0.0018 | 0.5497 | 0.0917 | 0.0523 | 0.6882 | 0.6820 | 0.4597 |

## Mean Delta vs Traffic-only

| scenario | delta_macro_f1 | delta_normal_fpr | delta_raw_ece | delta_temp_ece | delta_raw_brier | delta_temp_brier |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| weak_cti_concat | +0.0530 | -0.0165 | +0.0508 | +0.0628 | -0.1005 | -0.0981 |
| source_gate | +0.0813 | -0.0638 | +0.0357 | +0.0556 | -0.1330 | -0.1291 |
| cal_source_gate | +0.0869 | -0.0696 | +0.0415 | +0.0579 | -0.1367 | -0.1292 |
| random_cti | +0.0101 | -0.0030 | +0.0044 | +0.0005 | -0.0003 | -0.0003 |
| cal_random_source_gate | +0.0075 | -0.0062 | +0.0212 | +0.0018 | +0.0025 | +0.0000 |

## Key Comparisons

- `cal_source_gate` has the best mean Macro-F1 in this UNSW v0.6 run: 0.3029, compared with `source_gate` 0.2974, `weak_cti_concat` 0.2690, and `traffic_only` 0.2161.
- `cal_source_gate` lowers Normal FPR relative to traffic-only by -0.0696, and is slightly lower than plain `source_gate` by -0.0058.
- Calibration is not solved: `cal_source_gate` raw ECE is 0.1119, higher than plain `source_gate` 0.1061 and traffic-only 0.0704; temperature-scaled ECE is 0.1084, still much higher than traffic-only 0.0506.
- The stronger negative control is clean: `cal_source_gate` beats `cal_random_source_gate` by +0.0793 Macro-F1, so the gain is not reproduced by the same alpha-selection machinery over shuffled CTI hints.
- `cal_source_gate` selected alpha 1.25 for all three seeds, which means the validation rule preferred amplifying source-gated evidence; this should be interpreted together with the ECE penalty.

## Interpretation

- v0.6 strengthens the UNSW effectiveness/FPR story: training-time calibrated source gating improves Macro-F1 over v0.5-style source gate and over random-gated controls.
- v0.6 does not solve calibration. The method improves F1 and Normal FPR but remains overconfident relative to traffic-only under ECE/Brier-style evaluation.
- The manuscript should report v0.6 as a partial positive result with a calibration caveat, not as a solved reliability-calibration method.

## Evidence Files

- Raw result directory: `04_Results/cti_v06_calibrated_gate/`
- Kaggle output directory: `outputs/kaggle_trustfedfusion_v06_cal_gate/`
- Multi-seed table: `04_Results/tables/cti_v06_calibrated_gate_multiseed_summary.csv`
- Delta table: `04_Results/tables/cti_v06_calibrated_gate_deltas.csv`
