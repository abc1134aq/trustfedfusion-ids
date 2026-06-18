# NetFlow Near-Full Confirmation Summary

Source files: `04_Results/netflow_nearfull_confirm/` and `outputs/kaggle_trustfedfusion_netflow_nearfull/`. This is a per-family 100k capped confirmation, not full raw-dataset final performance.

## Multiseed Means

| Dataset | Scenario | Macro-F1 | Accuracy | Normal FPR | ECE | Brier |
|---|---|---:|---:|---:|---:|---:|
| `nf_bot_iot` | `random_cti` | 0.4492 | 0.4730 | 0.1372 | 0.0916 | 0.6025 |
| `nf_bot_iot` | `source_gate` | 0.4870 | 0.5371 | 0.0330 | 0.0694 | 0.5252 |
| `nf_bot_iot` | `traffic_only` | 0.4346 | 0.4612 | 0.1396 | 0.0976 | 0.6024 |
| `nf_bot_iot` | `weak_cti_concat` | 0.4928 | 0.5491 | 0.0353 | 0.0747 | 0.5260 |
| `nf_ton_iot` | `random_cti` | 0.2317 | 0.2894 | 0.3131 | 0.0706 | 0.7533 |
| `nf_ton_iot` | `source_gate` | 0.3760 | 0.4252 | 0.1598 | 0.1096 | 0.6624 |
| `nf_ton_iot` | `traffic_only` | 0.2121 | 0.2851 | 0.3131 | 0.0639 | 0.7529 |
| `nf_ton_iot` | `weak_cti_concat` | 0.3689 | 0.4054 | 0.2501 | 0.1059 | 0.6869 |

## Interpretation

- NF-ToN-IoT: `source_gate` is a strong near-full confirmation, with Macro-F1 0.3760 versus traffic-only 0.2121, weak CTI 0.3689, and random CTI 0.2317. Normal FPR also drops from 0.3131 to 0.1598. Calibration worsens versus traffic-only, so this is not a calibration win.
- NF-BoT-IoT: `source_gate` beats traffic-only and random CTI on Macro-F1 and has the best Normal FPR/ECE, but weak CTI concat has slightly higher Macro-F1: 0.4928 versus 0.4870.
- Random CTI remains close to traffic-only on both datasets, strengthening the claim that useful evidence is not merely extra dimensions.

Conclusion: NetFlow near-full strengthens cross-domain evidence, especially for source-gate operational FPR, but should be written as near-full per-family-capped confirmation with a weak-concat boundary on NF-BoT.
