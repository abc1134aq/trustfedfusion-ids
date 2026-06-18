# Edge-IIoT ML Full Robustness Summary

Generated from local full Edge-IIoT ML runs, 15 classes, 10 clients, label-skew non-IID, 10 communication rounds, seed 42.
Label-like leakage columns are excluded from features; in Edge-IIoT ML, `Attack_label` is skipped while `Attack_type` is the target.

Clean FedAvg/avg baseline: Accuracy 0.5077, Macro-F1 0.3821.

| Attack | Malicious ratio | Aggregator | Accuracy | Macro-F1 | Δ Macro-F1 vs clean FedAvg | Normal FPR | Comm MB/round | Avg round s |
| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| none | 0.0 | avg | 0.5077 | 0.3821 | 0.0000 | 0.0753 | 0.0652 | 0.0272 |
| label_flip | 0.1 | avg | 0.4446 | 0.3464 | -0.0356 | 0.5265 | 0.0652 | 0.0238 |
| label_flip | 0.1 | median | 0.3867 | 0.2660 | -0.1161 | 0.6905 | 0.0652 | 0.0241 |
| label_flip | 0.1 | trimmed_mean | 0.4432 | 0.2716 | -0.1105 | 0.1955 | 0.0652 | 0.0241 |
| label_flip | 0.1 | krum | 0.3150 | 0.2020 | -0.1800 | 0.5753 | 0.0652 | 0.0239 |
| label_flip | 0.2 | avg | 0.4420 | 0.3044 | -0.0777 | 0.6352 | 0.0652 | 0.0239 |
| label_flip | 0.2 | median | 0.3957 | 0.2901 | -0.0920 | 0.6549 | 0.0652 | 0.0244 |
| label_flip | 0.2 | trimmed_mean | 0.3949 | 0.2527 | -0.1293 | 0.5722 | 0.0652 | 0.0241 |
| label_flip | 0.2 | krum | 0.1831 | 0.0744 | -0.3076 | 1.0000 | 0.0652 | 0.0235 |
| label_flip | 0.3 | avg | 0.2524 | 0.2000 | -0.1820 | 0.9988 | 0.0652 | 0.0235 |
| label_flip | 0.3 | median | 0.2180 | 0.1505 | -0.2316 | 0.9998 | 0.0652 | 0.0237 |
| label_flip | 0.3 | trimmed_mean | 0.2082 | 0.1467 | -0.2353 | 0.9998 | 0.0652 | 0.0231 |
| label_flip | 0.3 | krum | 0.1831 | 0.0744 | -0.3076 | 1.0000 | 0.0652 | 0.0232 |
| update_scale | 0.1 | avg | 0.4150 | 0.2749 | -0.1072 | 0.1385 | 0.0652 | 0.0230 |
| update_scale | 0.1 | median | 0.4131 | 0.2309 | -0.1511 | 0.0037 | 0.0652 | 0.0231 |
| update_scale | 0.1 | trimmed_mean | 0.4150 | 0.2343 | -0.1477 | 0.0037 | 0.0652 | 0.0226 |
| update_scale | 0.1 | krum | 0.3150 | 0.2020 | -0.1800 | 0.5753 | 0.0652 | 0.0232 |
| update_scale | 0.2 | avg | 0.4645 | 0.3205 | -0.0615 | 0.0307 | 0.0652 | 0.0231 |
| update_scale | 0.2 | median | 0.4039 | 0.2249 | -0.1571 | 0.0037 | 0.0652 | 0.0231 |
| update_scale | 0.2 | trimmed_mean | 0.4344 | 0.2621 | -0.1200 | 0.0037 | 0.0652 | 0.0232 |
| update_scale | 0.2 | krum | 0.1831 | 0.0744 | -0.3076 | 1.0000 | 0.0652 | 0.0240 |
| update_scale | 0.3 | avg | 0.4916 | 0.3523 | -0.0298 | 0.0041 | 0.0652 | 0.0231 |
| update_scale | 0.3 | median | 0.4147 | 0.2384 | -0.1437 | 0.0037 | 0.0652 | 0.0227 |
| update_scale | 0.3 | trimmed_mean | 0.4409 | 0.2911 | -0.0909 | 0.0037 | 0.0652 | 0.0226 |
| update_scale | 0.3 | krum | 0.1831 | 0.0744 | -0.3076 | 1.0000 | 0.0652 | 0.0224 |

## Immediate Reading

- The no-leakage full 15-class Edge-IIoT ML task is difficult enough to expose real non-IID and attack sensitivity.
- Under label-skew non-IID, robust aggregation does not automatically dominate FedAvg; distance-based Krum is especially fragile when benign heterogeneous clients resemble outliers.
- The results justify the TrustFedFusion-IDS premise: the next method must calibrate evidence reliability and separate benign heterogeneity from malicious evidence/update anomalies.
