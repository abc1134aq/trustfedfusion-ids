# Kaggle CTI Adapter v0.3 MLP Summary

Kernel: `<kaggle-user>/trustfedfusion-cti-adapter-v03-mlp`.

## Core Multiseed Result

| Scenario | n | Macro-F1 mean | Macro-F1 std | Accuracy mean | Normal FPR mean | ECE mean | Brier mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| traffic_only | 3 | 0.0485 | 0.0083 | 0.0892 | 0.9552 | 0.1165 | 0.9752 |
| weak_cti_concat | 3 | 0.0348 | 0.0125 | 0.0629 | 0.9833 | 0.1855 | 1.0213 |
| source_gate_alpha0p5 | 3 | 0.0209 | 0.0165 | 0.0404 | 0.9523 | 0.2084 | 1.0349 |
| random_cti | 3 | 0.0354 | 0.0055 | 0.0529 | 0.9804 | 0.1944 | 1.0239 |

## Main Deltas

| Comparison | Metric | Delta |
|---|---|---:|
| weak_cti_concat - traffic_only | macro_f1 | -0.0137 |
| source_gate_alpha0p5 - traffic_only | macro_f1 | -0.0276 |
| source_gate_alpha0p5 - weak_cti_concat | macro_f1 | -0.0139 |
| random_cti - traffic_only | macro_f1 | -0.0131 |
| weak_cti_concat - traffic_only | normal_fpr | 0.0281 |
| source_gate_alpha0p5 - traffic_only | normal_fpr | -0.0029 |
| source_gate_alpha0p5 - weak_cti_concat | normal_fpr | -0.0310 |
| random_cti - traffic_only | normal_fpr | 0.0252 |
| weak_cti_concat - traffic_only | ece | 0.0690 |
| source_gate_alpha0p5 - traffic_only | ece | 0.0919 |
| source_gate_alpha0p5 - weak_cti_concat | ece | 0.0229 |
| random_cti - traffic_only | ece | 0.0779 |

## Interpretation

- v0.3 tests whether a non-linear NumPy MLP can use source-gated CTI evidence better than the v0.2 linear softmax model.
- Source gate still does not beat weak CTI concat on mean Macro-F1 in this MLP probe; this argues for a learned gate/TabTransformer or a narrower contribution.
- Random CTI remains close to traffic-only, supporting the negative-control sanity check.
