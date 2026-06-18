# CICIoT2023 Rare-Family Sampled Summary

Kernel: `<kaggle-user>/trustfedfusion-ciciot2023-rare-family`.

## Sampling Improvement

| Family | Previous sampled count | Rare-family count | Delta |
|---|---:|---:|---:|
| benign | 2500 | 3000 | 500 |
| brute_force | 567 | 2204 | 1637 |
| dos_ddos | 2500 | 3000 | 500 |
| malware | 150 | 594 | 444 |
| mirai | 2500 | 3000 | 500 |
| recon | 2500 | 3000 | 500 |
| spoofing_mitm | 2500 | 3000 | 500 |
| web_injection | 888 | 3000 | 2112 |

## Sample Boundary

- Rows read under bound: 8,026,781
- Sample rows: 20,798
- Label column: `label`
- Full dataset downloaded locally: `False`

## 3-Seed Result

| Scenario | n | Macro-F1 mean | Macro-F1 std | Accuracy mean | Normal FPR mean | ECE mean | Brier mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| traffic_only | 3 | 0.5619 | 0.0087 | 0.6024 | 0.4036 | 0.0620 | 0.4831 |
| weak_cti_concat | 3 | 0.5725 | 0.0108 | 0.6153 | 0.3111 | 0.0509 | 0.4664 |
| source_gate | 3 | 0.5722 | 0.0110 | 0.6148 | 0.3116 | 0.0504 | 0.4656 |
| random_cti | 3 | 0.5614 | 0.0084 | 0.6019 | 0.4062 | 0.0597 | 0.4841 |

## Main Deltas

- weak_cti_concat - traffic_only Macro-F1: `0.0106`
- source_gate - traffic_only Macro-F1: `0.0103`
- source_gate - weak_cti_concat Macro-F1: `-0.0003`
- random_cti - traffic_only Macro-F1: `-0.0006`
- source_gate - traffic_only Normal FPR: `-0.0920`

## Interpretation

- Rare-family bounded sampling improves coverage for brute_force, web_injection, and malware, though malware remains underrepresented.
- Weak CTI and source gate both improve over traffic-only; source gate is nearly tied with weak concat and slightly lower on mean Macro-F1.
- Random CTI remains near traffic-only, supporting the negative-control sanity check.
- This is still not a full-dataset CICIoT2023 result because it is bounded by row-read and family caps.
