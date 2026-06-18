# Kaggle Matrix v2 Summary

| method | aggregator | attack | malicious_ratio | rounds | accuracy | macro_f1 | fpr_normal | ece | brier | mean_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| fedavg | avg | label_flip | 0.2000 | 30 | 0.4777 | 0.3375 | 0.5401 | 0.0898 | 0.6517 | 0.3894 |
| fedavg | krum | label_flip | 0.2000 | 30 | 0.1885 | 0.0766 | 1.0000 | 0.3986 | 1.0975 | 0.5871 |
| fedavg | median | label_flip | 0.2000 | 30 | 0.4642 | 0.3463 | 0.5407 | 0.2384 | 0.7685 | 0.2259 |
| fedavg | trimmed_mean | label_flip | 0.2000 | 30 | 0.4538 | 0.3007 | 0.4634 | 0.1481 | 0.7294 | 0.3136 |
| fedavg | avg | none | 0.0000 | 50 | 0.5778 | 0.4681 | 0.0578 | 0.1173 | 0.5560 | 0.4605 |
| fedprox | avg | none | 0.0000 | 50 | 0.5777 | 0.4680 | 0.0576 | 0.1177 | 0.5564 | 0.4600 |
| fedavg | avg | update_scale | 0.2000 | 30 | 0.4953 | 0.3934 | 0.0463 | 0.0473 | 0.5956 | 0.4988 |
| fedavg | krum | update_scale | 0.2000 | 30 | 0.1885 | 0.0766 | 1.0000 | 0.3986 | 1.0975 | 0.5871 |
| fedavg | median | update_scale | 0.2000 | 30 | 0.4216 | 0.2502 | 0.0037 | 0.1069 | 0.7002 | 0.3348 |
| fedavg | trimmed_mean | update_scale | 0.2000 | 30 | 0.4684 | 0.3332 | 0.0037 | 0.0815 | 0.6295 | 0.4270 |
