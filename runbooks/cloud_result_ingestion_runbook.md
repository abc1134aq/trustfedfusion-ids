# Cloud Result Ingestion Runbook

Updated: 2026-06-15 23:58 +07

Purpose: keep the Kaggle-first workflow reproducible without storing large datasets locally or inventing result claims before outputs land.

## Active Jobs

| Job | Kernel | Last checked | Status | Claim boundary |
| --- | --- | --- | --- | --- |
| CTI v0.7 calibration objective | `<kaggle-user>/trustfedfusion-v07-cal-objective` | 2026-06-15 22:00 | `COMPLETE`, pulled | No ECE/Brier improvement claim; negative/neutral calibration result |
| NetFlow near-full confirmation | `<kaggle-user>/trustfedfusion-netflow-nearfull` | 2026-06-15 22:00 | `COMPLETE`, pulled | Strengthened per-family-capped NetFlow evidence, not full raw-dataset final |
| CTI v0.8 post-hoc calibration | `<kaggle-user>/trustfedfusion-v08-posthoc-calibration` | 2026-06-15 22:35 +07 | `COMPLETE`, pulled | Negative/neutral post-hoc calibration result; F1/FPR positive but ECE/Brier not solved |

## When A Job Completes

1. Pull Kaggle outputs into the matching `outputs/kaggle_trustfedfusion_*` directory. Done for v0.7, NetFlow near-full, and v0.8.
2. Copy validated result files into the matching `04_Results/` directory. Done.
3. Generate summary markdown, multiseed summary CSV, delta CSV, and per-family CSV where available. Done for summary/deltas.
4. Update `04_Results/tables/cross_dataset_evidence_matrix.md` and `.csv`. Done.
5. Update `06_Manuscript/contribution_claims.md`, `06_Manuscript/experiment_section_plan.md`, `05_Figures/figure_plan.md`, and `09_Project_Management/academic_integrity_plan.md`. Done.
6. If the result is mixed or negative, record it as a boundary/failure case rather than hiding it.

## Acceptance Checks

CTI v0.7 is useful only if `cal_source_gate_ece` keeps a meaningful Macro-F1/FPR gain while lowering temp ECE or Brier relative to v0.6 `cal_source_gate`, and remains higher than calibrated random-gate controls.

NetFlow near-full strengthens the paper only if `source_gate` stays above traffic-only and random CTI on Macro-F1 for both NF-ToN and NF-BoT, with Normal FPR not worsening enough to undermine the operational-risk claim.

CTI v0.8 is useful as a calibration-boundary result: gate-binned temperature scaling does not meaningfully lower source-gate ECE/Brier relative to scalar temperature, while the F1/FPR detection signal remains positive.

Formal abstract remains blocked until P17 closest-prior boundaries are stable and the manuscript decides whether calibration is framed as a limitation or a future mechanism.
