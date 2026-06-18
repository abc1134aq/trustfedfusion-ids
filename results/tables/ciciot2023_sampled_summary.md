# CICIoT2023 Sampled Cross-Domain Summary

Kernel: `<kaggle-user>/trustfedfusion-ciciot2023-sampled-cross-domain`.

## Sample Boundary

- Rows read under bound: 2,043,013
- Sample rows: 14,105
- Label column: `label`
- Full dataset downloaded locally: `False`
- Family counts: `{"benign": 2500, "brute_force": 567, "dos_ddos": 2500, "malware": 150, "mirai": 2500, "recon": 2500, "spoofing_mitm": 2500, "web_injection": 888}`

## 3-Seed Result

| Scenario | n | Macro-F1 mean | Macro-F1 std | Accuracy mean | Normal FPR mean | ECE mean | Brier mean |
|---|---:|---:|---:|---:|---:|---:|---:|
| traffic_only | 3 | 0.5320 | 0.0034 | 0.6541 | 0.4203 | 0.0909 | 0.4568 |
| weak_cti_concat | 3 | 0.5421 | 0.0060 | 0.6662 | 0.3659 | 0.0796 | 0.4424 |
| source_gate | 3 | 0.5430 | 0.0061 | 0.6650 | 0.3616 | 0.0753 | 0.4402 |
| random_cti | 3 | 0.5281 | 0.0044 | 0.6494 | 0.4219 | 0.0875 | 0.4582 |

## Main Deltas

- weak_cti_concat - traffic_only Macro-F1: `0.0102`
- source_gate - traffic_only Macro-F1: `0.0111`
- source_gate - weak_cti_concat Macro-F1: `0.0009`
- random_cti - traffic_only Macro-F1: `-0.0038`
- source_gate - traffic_only Normal FPR: `-0.0587`
- source_gate - weak_cti_concat ECE: `-0.0043`

## Interpretation

- CICIoT2023 sampled results support the cross-domain feasibility of observable CTI/protocol evidence.
- On this bounded sample, source_gate slightly beats weak_cti_concat on mean Macro-F1 and improves Normal FPR/ECE, but the margin is small and the sample is class-capped.
- Because brute_force, malware, and web_injection did not reach the per-family cap, this result must remain a probe until a fuller stratified sampling design is run.
- Random CTI stays near or below traffic-only, which supports the negative-control sanity check.
