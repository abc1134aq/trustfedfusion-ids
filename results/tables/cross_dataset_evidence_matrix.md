# Cross-Dataset Evidence Matrix

Purpose: consolidate positive, neutral, and negative evidence for TrustFedFusion-IDS without overclaiming.

| Evidence block | Scope | Traffic F1 | Weak CTI F1 | Source gate F1 | Random CTI F1 | Source delta vs traffic | Interpretation | Boundary |
|---|---|---:|---:|---:|---:|---:|---|---|
| Edge-IIoT linear FL v0.2 | Edge-IIoT clean full, 30 rounds x 3 seeds | 0.4508 | 0.4977 | 0.4706 | 0.4506 | +0.0198 | Weak CTI positive; source gate helps traffic/FPR but does not beat weak concat. | Linear FL only; source gate not final best on Edge. |
| Edge-IIoT centralized Torch MLP v0.4 | Edge-IIoT clean full, centralized MLP x 3 seeds | 0.8241 | 0.8245 | 0.8175 | 0.8168 | -0.0065 | Strong neural traffic baseline; CTI/source gate does not improve neural Edge result. | Neutral/negative for neural CTI claim. |
| CICIoT2023 rare-family sampled | CICIoT2023 bounded rare-family sample x 3 seeds | 0.5619 | 0.5725 | 0.5722 | 0.5614 | +0.0103 | Cross-domain sampled evidence supports weak/source CTI; source gate ties weak concat. | Bounded sample, not full CICIoT performance. |
| UNSW-NB15 official split | UNSW official train/test x 3 seeds | 0.2230 | 0.2628 | 0.2853 | 0.2330 | +0.0623 | Source gate positive on Macro-F1 and Normal FPR. | ECE worsens; random CTI gives small Macro-F1 gain, so causal claim must be cautious. |
| NF-ToN-IoT NetFlow stress | NF-ToN bounded per-family sample x 3 seeds | 0.2849 | 0.4489 | 0.4566 | 0.2986 | +0.1716 | Strongest positive source-gate evidence under sparse NetFlow features. | Bounded stress probe, not full-dataset final result. |
| NF-BoT-IoT NetFlow stress | NF-BoT bounded per-family sample x 3 seeds | 0.4895 | 0.5659 | 0.5759 | 0.4954 | +0.0865 | Positive source-gate evidence with cleaner random negative control. | Bounded stress probe, not full-dataset final result. |
| NF-ToN-IoT NetFlow near-full | NF-ToN per-family 100k cap x 3 seeds | 0.2121 | 0.3689 | 0.3760 | 0.2317 | +0.1639 | Strong near-full confirmation: source gate beats traffic, weak concat, and random CTI on Macro-F1 and lowers Normal FPR. | Per-family capped, not full raw-dataset final; ECE worsens vs traffic-only. |
| NF-BoT-IoT NetFlow near-full | NF-BoT per-family 100k cap x 3 seeds | 0.4346 | 0.4928 | 0.4870 | 0.4492 | +0.0524 | Source gate beats traffic/random and has best Normal FPR/ECE, but weak concat has slightly higher Macro-F1. | Per-family capped; source gate is not uniformly best on F1. |
| UNSW-NB15 v0.5 calibrated | UNSW official train/test, train-core validation calibration x 3 seeds | 0.2161 | 0.2690 | 0.2974 | 0.2261 | +0.0813 | Source gate remains strongest after adding validation calibration protocol. | Temperature scaling and raw-hint pruning do not fix source-gate ECE; local and Kaggle replay complete. |
| UNSW-NB15 v0.6 calibrated gate | UNSW official train/test, validation-selected alpha x 3 seeds | 0.2161 | 0.2690 | 0.3029 | 0.2261 | +0.0869 | Training-time alpha-selected source gate improves UNSW Macro-F1 and Normal FPR; `cal_random_source_gate` stays low at 0.2236. | Calibration still not solved: temp ECE 0.1084 vs traffic 0.0506; partial positive result only. |
| UNSW-NB15 v0.7 calibration objective | UNSW official train/test, composite ECE/Brier alpha objective x 3 seeds | 0.2161 | n/a | 0.3029 | 0.2261 | +0.0869 | v0.7 preserves the v0.6 F1/FPR positive result and beats calibrated random-gate controls. | Negative/neutral calibration result: `cal_source_gate_ece` is identical to `cal_source_gate`, temp ECE remains 0.1084. |
| UNSW-NB15 v0.8 post-hoc calibration | UNSW official train/test, source-gate-binned temperature scaling x 3 seeds | 0.2161 | n/a | 0.3029 | 0.2261 | +0.0869 | v0.8 preserves the source-gate detection/FPR result and tests scalar/group2/group3 post-hoc calibration. | Negative/neutral calibration result: group3 ECE only changes `cal_source_gate` from 0.1084 to 0.1067 and Brier does not support a solved-calibration claim. |

## Current Claim Discipline

- Supported: weak/source evidence often improves over traffic-only across sampled cross-domain datasets.
- Supported: source gate is strongest on UNSW and NetFlow stress probes, especially for Normal FPR.
- Supported: v0.6 validation-selected source gate strengthens the UNSW effectiveness/FPR result and beats the calibrated random-gate control.
- Supported: NetFlow near-full confirmation strengthens cross-domain evidence; NF-ToN source gate remains best on Macro-F1/FPR, while NF-BoT source gate has best FPR/ECE but slightly trails weak concat on Macro-F1.
- Supported: v0.7 is a useful negative result for calibration-objective tuning: it does not improve over v0.6 on ECE/Brier.
- Supported: v0.8 is a useful negative/neutral result for post-hoc source-aware calibration: binned temperature scaling does not solve source-gate ECE/Brier.
- Not supported: source gate is universally best, because Edge linear v0.2 trails weak concat and Edge neural v0.4 is neutral/negative.
- Not supported: calibration-aware source gating is solved, because v0.5, v0.6, v0.7, and v0.8 leave source-gate ECE high relative to traffic-only.
- Not supported: final full-dataset cross-domain performance, because CICIoT and NetFlow runs are still bounded or per-family-capped probes.
- Required next: either a stronger calibration mechanism or a narrower contribution that treats calibration as an evaluated limitation rather than a solved module.
