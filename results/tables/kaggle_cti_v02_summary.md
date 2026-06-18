# Kaggle CTI Adapter v0.2 Summary

Kernel: `<kaggle-user>/trustfedfusion-cti-adapter-v02`.

## Core Multiseed Result

| Scenario | n | Macro-F1 mean | Macro-F1 std | Accuracy mean | Normal FPR mean | ECE mean | Brier mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| traffic_only | 3 | 0.4508 | 0.0123 | 0.5643 | 0.0545 | 0.1284 | 0.5767 |
| weak_cti_concat | 3 | 0.4977 | 0.0080 | 0.6049 | 0.0580 | 0.1256 | 0.5360 |
| source_gate_alpha0p5 | 3 | 0.4706 | 0.0211 | 0.5849 | 0.0413 | 0.1138 | 0.5426 |
| random_cti | 3 | 0.4506 | 0.0118 | 0.5632 | 0.0574 | 0.1271 | 0.5769 |

## Main Deltas

| Comparison | Metric | Delta |
|---|---|---:|
| weak_cti_concat - traffic_only | macro_f1 | 0.0469 |
| source_gate_alpha0p5 - traffic_only | macro_f1 | 0.0198 |
| source_gate_alpha0p5 - weak_cti_concat | macro_f1 | -0.0271 |
| random_cti - traffic_only | macro_f1 | -0.0002 |
| weak_cti_concat - traffic_only | normal_fpr | 0.0034 |
| source_gate_alpha0p5 - traffic_only | normal_fpr | -0.0132 |
| source_gate_alpha0p5 - weak_cti_concat | normal_fpr | -0.0167 |
| random_cti - traffic_only | normal_fpr | 0.0029 |
| weak_cti_concat - traffic_only | ece | -0.0027 |
| source_gate_alpha0p5 - traffic_only | ece | -0.0146 |
| source_gate_alpha0p5 - weak_cti_concat | ece | -0.0118 |
| random_cti - traffic_only | ece | -0.0013 |

## Seed-42 Probes

| Scenario | Macro-F1 | Accuracy | Normal FPR | ECE | Brier |
|---|---:|---:|---:|---:|---:|
| reliability_gate_alpha0p5 | 0.4677 | 0.5850 | 0.0420 | 0.1068 | 0.5388 |
| source_gate_alpha0p25 | 0.4511 | 0.5741 | 0.0358 | 0.0992 | 0.5415 |
| source_gate_alpha0p5_drop0p3 | 0.4675 | 0.5770 | 0.0409 | 0.1218 | 0.5578 |
| source_gate_alpha0p5_poison0p2 | 0.4529 | 0.5697 | 0.0607 | 0.1143 | 0.5599 |
| source_gate_alpha0p75 | 0.4515 | 0.5742 | 0.0360 | 0.0997 | 0.5416 |

## Interpretation

- Source-specific gating improves over traffic-only in this linear NumPy setup.
- Source-specific gating still does not beat plain weak CTI concat on Macro-F1 in the 3-seed mean.
- The method claim should stay conservative: reliability/source gates are useful for calibration and robustness analysis, but are not yet the final best-performing fusion mechanism.
- The next methodological move is a non-linear model or learned gate, plus sampled cross-domain confirmation on CICIoT2023.
