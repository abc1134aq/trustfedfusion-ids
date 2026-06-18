# Full Manuscript Claim Audit After Figure 4 Integration

Updated: 2026-06-16 02:00 +07

Scope:

- `06_Manuscript/working_manuscript_no_abstract_v1.md`
- `06_Manuscript/sections/results_draft_v1.md`
- `06_Manuscript/table4_claim_evidence_gate.md`
- `06_Manuscript/claim_evidence_registry.md`
- `05_Figures/figure4_publication_draft.pdf`
- `05_Figures/figure4_cross_dataset_data.csv`

Status: pass for internal no-abstract manuscript use. This is not a submission clearance because P17 full text, final Elsevier formatting, repository DOI/accession, and final template-scale figure QA remain open.

## Audit Summary

| Check | Result | Evidence |
|---|---|---|
| Figure 4 integrated into Results | Pass | Results now references Figure 4A-B for cross-dataset mixed evidence and Figure 4C-D for calibration-boundary evidence. |
| No solved-calibration claim | Pass | Results says ECE/Brier are not solved and treats calibration as an evaluated limitation. |
| No P17 superiority claim | Pass | Results says the evidence does not support superiority over P17/FedKD-IDS. |
| No P17 absence claim | Pass | P17 fields remain unknown because full text is missing. |
| No full raw-dataset overclaim | Pass | CICIoT is sampled/rare-family sampled; NetFlow near-full is per-family capped. |
| No production CTI or label-to-TTP input claim | Pass | Weak CTI is defined as protocol/source-derived or controlled hints; true `Attack_type -> TTP/family` evidence is blocked. |
| Positive, neutral, and negative evidence visible | Pass | Edge neural neutral/negative result, NF-BoT weak-concat boundary, random CTI caveat, Krum collapse, and calibration failure remain in the draft. |

## Figure 4-Specific Claim Gate

Allowed wording:

- "Figure 4 summarizes cross-dataset evidence and calibration boundaries."
- "Weak/source evidence often improves over traffic-only in bounded settings."
- "Source gate is not uniformly the top Macro-F1 variant."
- "Calibration remains unresolved through v0.8."
- "CICIoT and NetFlow results are sampled, stress, or per-family-capped rather than full raw-dataset final performance."

Blocked wording:

- "TrustFedFusion-IDS is better than P17/FedKD-IDS."
- "P17 lacks CTI, calibration, or cross-domain evaluation."
- "TrustFedFusion-IDS solves calibration."
- "Source gate is universally best."
- "CICIoT/NetFlow results are full raw-dataset final results."
- "The method uses production CTI feeds or true label-to-TTP mappings."

## Remaining Gates Before Formal Abstract

1. P17 must either remain metadata-only in the abstract or a legal full text/author manuscript must land.
2. Final figure scaling must be checked after Elsevier template assembly.
3. Data/code repository DOI or stable accession remains missing.
4. Formal abstract must be drafted from Table 4 READY/PARTIAL rows only.
5. Any new experiment, especially CTI v0.9, must update `claim_evidence_registry.md` before it can affect the abstract.

## Decision

The no-abstract working manuscript can continue to internal review with Figure 4 included. The formal abstract should remain closed.
