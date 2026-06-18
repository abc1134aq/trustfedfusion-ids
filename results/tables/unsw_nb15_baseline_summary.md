# UNSW-NB15 Bounded Baseline Summary

Status: complete and pulled from Kaggle. This uses the official UNSW-NB15 train/test split and train-fitted preprocessing.

## Multi-seed Core Metrics

| scenario | accuracy_mean | accuracy_std | macro_f1_mean | macro_f1_std | normal_fpr_mean | normal_fpr_std | ece_mean | brier_mean | mean_confidence_mean |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| random_cti | 0.4846 | 0.0012 | 0.2330 | 0.0026 | 0.5307 | 0.0004 | 0.0777 | 0.6790 | 0.4140 |
| source_gate | 0.5470 | 0.0007 | 0.2853 | 0.0019 | 0.4852 | 0.0004 | 0.1066 | 0.5482 | 0.5962 |
| traffic_only | 0.4840 | 0.0014 | 0.2230 | 0.0008 | 0.5259 | 0.0019 | 0.0753 | 0.6791 | 0.4133 |
| weak_cti_concat | 0.5139 | 0.0002 | 0.2628 | 0.0013 | 0.5384 | 0.0001 | 0.1087 | 0.5793 | 0.5377 |

## Mean Delta vs Traffic-only

| scenario | delta_accuracy_vs_traffic | delta_macro_f1_vs_traffic | delta_normal_fpr_vs_traffic | delta_ece_vs_traffic | delta_brier_vs_traffic |
| --- | ---: | ---: | ---: | ---: | ---: |
| random_cti | +0.0007 | +0.0100 | +0.0048 | +0.0023 | -0.0000 |
| source_gate | +0.0630 | +0.0623 | -0.0407 | +0.0313 | -0.1309 |
| weak_cti_concat | +0.0299 | +0.0398 | +0.0125 | +0.0334 | -0.0998 |

## Interpretation

- Source gate is the strongest UNSW setting in this softmax baseline: mean Macro-F1 0.2853 versus traffic-only 0.2230 and weak CTI 0.2628.
- Source gate also reduces Normal FPR relative to traffic-only by mean -0.0407, while weak CTI increases Normal FPR by mean +0.0125.
- Calibration worsens for weak/source CTI: ECE rises from 0.0753 traffic-only to 0.1087 weak CTI and 0.1066 source gate.
- Random CTI improves slightly over traffic-only (Macro-F1 +0.0100), so the negative control is not perfectly neutral on UNSW. Treat the stronger source-gate gain as promising but not sufficient for a causal CTI claim.
- This result strengthens cross-domain feasibility but still needs NF-ToN/NF-BoT stress tests and a calibration-aware gate redesign.

## Evidence Files

- Raw output directory: `outputs/kaggle_trustfedfusion_unsw_nb15/`
- Main result directory: `04_Results/unsw_nb15_baseline/`
- Multi-seed table: `04_Results/tables/unsw_nb15_baseline_multiseed_summary.csv`
- Delta table: `04_Results/tables/unsw_nb15_baseline_deltas.csv`
- Per-family table: `04_Results/tables/unsw_nb15_baseline_per_family_summary.csv`
