#!/usr/bin/env python3
"""Prepare a Kaggle-friendly Edge-IIoT ML CSV without label leakage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


LABEL_COL = "Attack_type"
LABEL_LIKE = {
    "attack_label",
    "attack_type",
    "attack_label",
    "label",
    "class",
    "attack_cat",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="02_Data/kaggle/edge_iiot_ml/ML-EdgeIIoT-dataset.csv")
    parser.add_argument("--output-dir", default="02_Data/processed")
    parser.add_argument("--sample-size", type=int, default=0)
    parser.add_argument("--max-cat-unique", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path, low_memory=False)
    if LABEL_COL not in df.columns:
        raise ValueError(f"Expected label column {LABEL_COL!r}, found {list(df.columns)}")

    selected_cols = [LABEL_COL]
    dropped_cols: dict[str, str] = {}
    for col in df.columns:
        if col == LABEL_COL:
            continue
        if col.lower() in LABEL_LIKE:
            dropped_cols[col] = "label-like column"
            continue

        numeric = pd.to_numeric(df[col], errors="coerce")
        if float(numeric.notna().mean()) >= 0.90:
            df[col] = numeric
            selected_cols.append(col)
            continue

        nunique = int(df[col].astype(str).nunique(dropna=True))
        if 1 < nunique <= args.max_cat_unique:
            selected_cols.append(col)
        else:
            dropped_cols[col] = f"high-cardinality nonnumeric column ({nunique} unique values)"

    clean = df[selected_cols].copy()
    full_path = output_dir / "edge_iiot_ml_clean_full.csv"
    clean.to_csv(full_path, index=False)

    sample_path = None
    if args.sample_size and args.sample_size > 0 and args.sample_size < len(clean):
        fractions = clean[LABEL_COL].value_counts(normalize=True)
        sample_parts = []
        for label, fraction in fractions.items():
            part = clean[clean[LABEL_COL] == label]
            n_label = min(len(part), max(1, round(args.sample_size * float(fraction))))
            sample_parts.append(part.sample(n_label, random_state=args.seed))
        sample = (
            pd.concat(sample_parts, axis=0)
            .sample(frac=1.0, random_state=args.seed)
            .reset_index(drop=True)
        )
        sample_path = output_dir / f"edge_iiot_ml_clean_{len(sample)}.csv"
        sample.to_csv(sample_path, index=False)

    summary = {
        "input": str(input_path),
        "full_output": str(full_path),
        "sample_output": str(sample_path) if sample_path else None,
        "rows": int(len(clean)),
        "columns": int(clean.shape[1]),
        "label_col": LABEL_COL,
        "labels": sorted(clean[LABEL_COL].astype(str).unique().tolist()),
        "selected_columns": selected_cols,
        "dropped_columns": dropped_cols,
        "leakage_guard": "label-like columns are excluded from features",
    }
    summary_path = output_dir / "edge_iiot_ml_clean_manifest.json"
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
