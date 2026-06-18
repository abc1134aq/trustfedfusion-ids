# CTI v0.8 Post-hoc Calibration Summary
Source files: `04_Results/cti_v08_posthoc_calibration/` and `outputs/kaggle_trustfedfusion_v08_posthoc_calibration/`.
This run keeps the v0.7 classifier/alpha-selection protocol and adds validation-only scalar, group2, and group3 temperature scaling. Macro-F1 is based on raw logits; temperature scaling only affects calibration metrics.
## Multiseed Means
| Scenario | Macro-F1 | Accuracy | Normal FPR | Raw ECE | Scalar ECE | Group2 ECE | Group3 ECE | Raw Brier | Scalar Brier | Group3 Brier | Mean alpha |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `cal_random_source_gate` | 0.2236 | 0.4724 | 0.5497 | 0.0917 | 0.0523 | 0.0523 | 0.0523 | 0.6882 | 0.6820 | 0.6820 | 0.42 |
| `cal_random_source_gate_ece` | 0.2297 | 0.4727 | 0.5502 | 0.0915 | 0.0549 | 0.0549 | 0.0549 | 0.6886 | 0.6826 | 0.6826 | 1.08 |
| `cal_source_gate` | 0.3029 | 0.5513 | 0.4863 | 0.1119 | 0.1084 | 0.1084 | 0.1067 | 0.5491 | 0.5527 | 0.5506 | 1.25 |
| `cal_source_gate_ece` | 0.3029 | 0.5513 | 0.4863 | 0.1119 | 0.1084 | 0.1084 | 0.1067 | 0.5491 | 0.5527 | 0.5506 | 1.25 |
| `random_cti` | 0.2261 | 0.4720 | 0.5529 | 0.0749 | 0.0511 | 0.0511 | 0.0511 | 0.6855 | 0.6817 | 0.6817 | 1.00 |
| `source_gate` | 0.2974 | 0.5459 | 0.4921 | 0.1061 | 0.1061 | 0.1061 | 0.1051 | 0.5528 | 0.5528 | 0.5544 | 1.00 |
| `traffic_only` | 0.2161 | 0.4675 | 0.5559 | 0.0704 | 0.0506 | 0.0506 | 0.0506 | 0.6858 | 0.6819 | 0.6819 | 1.00 |

## Interpretation

- Detection/FPR signal remains positive: `cal_source_gate` reaches Macro-F1 0.3029 and Normal FPR 0.4863, versus traffic-only Macro-F1 0.2161 and Normal FPR 0.5559.
- The calibrated random control remains low on detection quality: `cal_random_source_gate` Macro-F1 is 0.2236.
- Calibration is not solved. `cal_source_gate` scalar ECE is 0.1084, still far above traffic-only scalar ECE 0.0506.
- Group3 source-binned temperature scaling only slightly lowers `cal_source_gate` ECE from 0.1084 to 0.1067; this is a small delta, not a method-level calibration breakthrough.
- Brier score does not support a clean calibration-success claim: `cal_source_gate` raw Brier is 0.5491, scalar Brier is 0.5527, and group3 Brier is 0.5506.

Conclusion: v0.8 should be reported as a partial positive effectiveness/FPR result with a negative/neutral post-hoc calibration finding. The paper should not claim source-aware calibration is solved.
