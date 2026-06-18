# Kaggle T1 FedGuard MVP Real-Data Baseline Note

Source kernel: `<kaggle-user>/t1-fedguard-mvp-real-data-baseline`  
Pulled output directory: `outputs/kaggle_t1_fedguard_mvp_real_data_baseline/`  
Copied summary table: `04_Results/tables/kaggle_t1_fedguard_mvp_real_data_baseline_mean_std_metrics.csv`

## Status

This run is complete and useful as an auxiliary baseline, but it is not the main TrustFedFusion-IDS result set.

Reason:

- Dataset setting is `Edge-IIoTset-light`, capped at `max_rows=100000` and `max_rows_per_class=5000`.
- Training is a 5-round MLP/proxy experiment with methods including `tifedguard_lite`, `tifedguard_no_proto`, and `tifedguard_no_norm`.
- The current TrustFedFusion mainline is the full clean Edge-IIoT ML CSV plus CTI v0/v0.1 no-label-leakage experiments.

## Key Numbers From Multiseed Summary

| Method | Setting | Macro-F1 mean | Macro-F1 std | Notes |
|---|---|---:|---:|---|
| centralized | clean | 0.5750 | 0.0262 | Upper-bound style reference |
| fedavg | clean | 0.4606 | 0.0235 | Comparable to early full-data FedAvg scale but different split/model |
| fedprox | clean | 0.4620 | 0.0245 | Similar to FedAvg |
| tifedguard_lite | clean | 0.4392 | 0.0054 | Does not beat FedAvg clean |
| tifedguard_lite | poison 0.3 | 0.3883 | 0.0493 | Higher retention than FedAvg poison 0.3 in this auxiliary setup |

## Manuscript Use

Use only as exploratory evidence for robust/proxy design ideas. Do not merge it into the main CTI v0.1 table unless the dataset cap, split, model, rounds, and method definitions are fully aligned.
