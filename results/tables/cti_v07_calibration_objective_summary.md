# CTI v0.7 Calibration Objective Summary

Source files: `04_Results/cti_v07_calibration_objective/` and `outputs/kaggle_trustfedfusion_v07_cal_objective/`.

## Multiseed Means

| Scenario | Macro-F1 | Accuracy | Normal FPR | Temp ECE | Temp Brier | Mean alpha |
|---|---:|---:|---:|---:|---:|---:|
| `cal_random_source_gate` | 0.2236 | 0.4724 | 0.5497 | 0.0523 | 0.6820 | 0.42 |
| `cal_random_source_gate_ece` | 0.2297 | 0.4727 | 0.5502 | 0.0549 | 0.6826 | 1.08 |
| `cal_source_gate` | 0.3029 | 0.5513 | 0.4863 | 0.1084 | 0.5527 | 1.25 |
| `cal_source_gate_ece` | 0.3029 | 0.5513 | 0.4863 | 0.1084 | 0.5527 | 1.25 |
| `random_cti` | 0.2261 | 0.4720 | 0.5529 | 0.0511 | 0.6817 | 1.00 |
| `source_gate` | 0.2974 | 0.5459 | 0.4921 | 0.1061 | 0.5528 | 1.00 |
| `traffic_only` | 0.2161 | 0.4675 | 0.5559 | 0.0506 | 0.6819 | 1.00 |

## Interpretation

- `cal_source_gate_ece` is numerically identical to `cal_source_gate` on the key metrics: Macro-F1 0.3029, Normal FPR 0.4863, temp ECE 0.1084, temp Brier 0.5527.
- Therefore v0.7 does not fix the v0.6 calibration caveat; the composite objective selected the same effective alpha in this run.
- The positive part remains effectiveness/FPR: calibrated source gating stays well above traffic-only Macro-F1 0.2161 and calibrated random-gate Macro-F1 0.2236.
- The limitation remains calibration: temp ECE 0.1084 is much higher than traffic-only 0.0506.

Conclusion: v0.7 should be reported as a negative/neutral calibration-objective result, not as a successful calibration fix.
