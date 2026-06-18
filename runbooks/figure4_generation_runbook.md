# Figure 4 Generation Runbook

Updated: 2026-06-16 02:45 +07

Status: portable release-candidate instructions. The project generated Figure 4 with the Python backend; this runbook explains how to regenerate it from the release package.

## Source Files

- Script: `code/figures/plot_figure4.py`
- Input CSV: `figures/source_data/figure4_cross_dataset_data.csv`
- Default output prefix: `figures/final_assets/figure4_publication_draft`

## Runtime

Install the release environment first:

```bash
python -m pip install -r environment/requirements.txt
```

Then check the plotting entry point:

```bash
python code/figures/plot_figure4.py --help
```

## Generation Command

Regeneration command:

```bash
python \
  code/figures/plot_figure4.py \
  --input figures/source_data/figure4_cross_dataset_data.csv \
  --output-prefix figures/final_assets/figure4_publication_draft
```

Generated outputs:

- `figures/final_assets/figure4_publication_draft.svg`
- `figures/final_assets/figure4_publication_draft.pdf`
- `figures/final_assets/figure4_publication_draft.png`

## QA Performed After Generation

1. Confirm that the SVG/PDF/PNG files are non-empty.
2. Render the PDF to PNG if visual QA tooling is available.
3. Check that Panel A does not imply source gate is universally best.
4. Check that Panel D states calibration remains unresolved.
5. Confirm sampled/per-family-capped boundaries appear in the figure footer and caption.

## Integrity Boundaries

Figure 4 must not claim:

- source gate is universally best;
- calibration has been fully resolved;
- full raw-dataset CICIoT/NetFlow final performance;
- production CTI feed effectiveness;
- label-derived TTP or family features as model input;
- TrustFedFusion-IDS superiority over P17/FedKD-IDS.
