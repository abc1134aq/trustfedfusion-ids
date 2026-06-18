# NF-ToN/NF-BoT NetFlow Stress Summary

Status: complete and pulled from Kaggle. This is a bounded per-family sampled NetFlow stress probe, not full-dataset final performance.

## Multi-seed Core Metrics

| dataset | scenario | accuracy_mean | accuracy_std | macro_f1_mean | macro_f1_std | normal_fpr_mean | normal_fpr_std | ece_mean | brier_mean |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| nf_bot_iot | random_cti | 0.5090 | 0.0043 | 0.4954 | 0.0028 | 0.1304 | 0.0040 | 0.0700 | 0.5545 |
| nf_bot_iot | source_gate | 0.6026 | 0.0058 | 0.5759 | 0.0064 | 0.0376 | 0.0029 | 0.0484 | 0.4616 |
| nf_bot_iot | traffic_only | 0.5018 | 0.0068 | 0.4895 | 0.0056 | 0.1304 | 0.0040 | 0.0666 | 0.5544 |
| nf_bot_iot | weak_cti_concat | 0.6019 | 0.0049 | 0.5659 | 0.0107 | 0.0514 | 0.0070 | 0.0666 | 0.4678 |
| nf_ton_iot | random_cti | 0.3753 | 0.0040 | 0.2986 | 0.0030 | 0.3119 | 0.0028 | 0.1067 | 0.7104 |
| nf_ton_iot | source_gate | 0.5335 | 0.0077 | 0.4566 | 0.0085 | 0.1618 | 0.0031 | 0.0862 | 0.5928 |
| nf_ton_iot | traffic_only | 0.3782 | 0.0051 | 0.2849 | 0.0035 | 0.3118 | 0.0028 | 0.1028 | 0.7100 |
| nf_ton_iot | weak_cti_concat | 0.5259 | 0.0003 | 0.4489 | 0.0011 | 0.2542 | 0.0009 | 0.1120 | 0.6156 |

## Mean Delta vs Traffic-only

| dataset | scenario | delta_accuracy_vs_traffic | delta_macro_f1_vs_traffic | delta_normal_fpr_vs_traffic | delta_ece_vs_traffic | delta_brier_vs_traffic |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| nf_bot_iot | random_cti | +0.0071 | +0.0060 | +0.0000 | +0.0034 | +0.0000 |
| nf_bot_iot | source_gate | +0.1008 | +0.0865 | -0.0928 | -0.0183 | -0.0928 |
| nf_bot_iot | weak_cti_concat | +0.1001 | +0.0765 | -0.0790 | -0.0000 | -0.0866 |
| nf_ton_iot | random_cti | -0.0029 | +0.0136 | +0.0001 | +0.0039 | +0.0004 |
| nf_ton_iot | source_gate | +0.1554 | +0.1716 | -0.1500 | -0.0165 | -0.1172 |
| nf_ton_iot | weak_cti_concat | +0.1477 | +0.1640 | -0.0576 | +0.0093 | -0.0944 |

## Interpretation

- NF-ToN: source gate improves Macro-F1 by +0.1717 over traffic-only and reduces Normal FPR by -0.1500; weak CTI improves Macro-F1 by +0.1640 but less FPR reduction.
- NF-BoT: source gate improves Macro-F1 by +0.0864 and reduces Normal FPR by -0.0928; weak CTI improves Macro-F1 by +0.0764 and reduces Normal FPR by -0.0790.
- Random CTI stays close to traffic-only on both datasets, especially NF-BoT; this is a cleaner negative control than UNSW.
- NetFlow results support the claim that source-gated weak evidence can help in sparse cross-domain settings, but these remain bounded sampled probes.

## Evidence Files

- Raw output directory: `outputs/kaggle_trustfedfusion_netflow_stress/`
- Main result directory: `04_Results/netflow_stress/`
- Multi-seed table: `04_Results/tables/netflow_stress_multiseed_summary.csv`
- Delta table: `04_Results/tables/netflow_stress_deltas.csv`
- Per-family table: `04_Results/tables/netflow_stress_per_family_summary.csv`
