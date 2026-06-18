# Kaggle CTI Adapter v0.1 Summary

Source kernel: `<kaggle-user>/trustfedfusion-cti-adapter-v0-1`.

## Core 30-round multi-seed results

| scenario | macro_f1_mean | macro_f1_std | accuracy_mean | fpr_normal_mean | ece_mean | brier_mean | comm_mb_round_mean |
| --- | --- | --- | --- | --- | --- | --- | --- |
| traffic_only | 0.4508 | 0.0123 | 0.5643 | 0.0545 | 0.1284 | 0.5767 | 0.0652 |
| weak_cti_concat | 0.4977 | 0.0080 | 0.6049 | 0.0580 | 0.1256 | 0.5360 | 0.0858 |
| reliability_gate_alpha0p5 | 0.4843 | 0.0151 | 0.5941 | 0.0497 | 0.1195 | 0.5397 | 0.1076 |
| random_cti | 0.4506 | 0.0118 | 0.5632 | 0.0574 | 0.1271 | 0.5769 | 0.0858 |

## Seed 42 scenario and robustness probes

| scenario | macro_f1 | accuracy | fpr_normal | ece | brier | family_dos_ddos_recall | family_reconnaissance_recall | family_injection_recall | family_malware_credential_recall | family_mitm_recall | family_normal_recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| random_cti | 0.4402 | 0.5575 | 0.0473 | 0.1204 | 0.5762 | 0.7963 | 0.7404 | 0.2233 | 0.2565 | 0.2840 | 0.9527 |
| reliability_gate_alpha0p25 | 0.4642 | 0.5827 | 0.0420 | 0.1041 | 0.5389 | 0.8018 | 0.8049 | 0.2782 | 0.2972 | 0.2840 | 0.9580 |
| reliability_gate_alpha0p5 | 0.4677 | 0.5850 | 0.0420 | 0.1068 | 0.5388 | 0.8013 | 0.8056 | 0.2775 | 0.3123 | 0.2840 | 0.9580 |
| reliability_gate_alpha0p5_drop0p3 | 0.4761 | 0.5834 | 0.0438 | 0.1273 | 0.5565 | 0.7939 | 0.7659 | 0.2418 | 0.3375 | 0.9547 | 0.9562 |
| reliability_gate_alpha0p5_poison0p2 | 0.4728 | 0.5803 | 0.0663 | 0.1222 | 0.5576 | 0.7982 | 0.7486 | 0.2644 | 0.3314 | 0.7449 | 0.9337 |
| reliability_gate_alpha0p75 | 0.4719 | 0.5880 | 0.0420 | 0.1103 | 0.5388 | 0.8013 | 0.8066 | 0.2778 | 0.3285 | 0.2840 | 0.9580 |
| traffic_only | 0.4396 | 0.5574 | 0.0469 | 0.1205 | 0.5760 | 0.7964 | 0.7385 | 0.2205 | 0.2530 | 0.2840 | 0.9531 |
| weak_cti_concat | 0.4892 | 0.6033 | 0.0438 | 0.1212 | 0.5355 | 0.8028 | 0.7758 | 0.2809 | 0.4224 | 0.2840 | 0.9562 |

## Integrity notes

- These are pulled Kaggle outputs, copied into `04_Results/metrics` with `kaggle_cti_v01_` prefixes.
- The reliability gate improves over traffic-only, but in the current NumPy linear setup it is below weak CTI concat on Macro-F1. This should be reported honestly, not hidden.
- Random CTI is not a stable positive control failure in all seeds; it is close to or above traffic-only in some runs, so the CTI adapter needs stronger leakage/noise diagnostics before any strong causal claim.
- Next experiments should test a non-linear PyTorch model, no-calibration/temperature scaling, source-specific gates, and cross-domain CICIoT sampled training/evaluation.
