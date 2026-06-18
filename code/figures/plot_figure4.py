#!/usr/bin/env python3
"""Generate Figure 4 from the audited cross-dataset CSV.

This script is prepared for the Python backend path. It should be run only
after the Figure 4 backend gate is explicitly set to Python.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


VARIANT_COLORS = {
    "traffic_only": "#4D4D4D",
    "weak_cti": "#0072B2",
    "source_gate": "#009E73",
    "random_cti": "#CC79A7",
}


def parse_float(value: str) -> float | None:
    value = (value or "").strip()
    if not value:
        return None
    return float(value)


def load_rows(path: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            row: dict[str, object] = dict(raw)
            for key in [
                "traffic_only",
                "weak_cti",
                "source_gate",
                "random_cti",
                "source_delta_vs_traffic",
                "source_delta_vs_weak",
            ]:
                row[key] = parse_float(str(raw.get(key, "")))
            rows.append(row)
    return rows


def require_rows(rows: list[dict[str, object]], panel: str) -> list[dict[str, object]]:
    selected = [row for row in rows if row["panel"] == panel]
    if not selected:
        raise ValueError(f"No rows found for panel {panel}")
    return selected


def short_label(evidence_block: str) -> str:
    replacements = {
        "Edge-IIoT linear FL v0.2": "Edge linear",
        "Edge-IIoT centralized Torch MLP v0.4": "Edge MLP",
        "CICIoT2023 rare-family sampled": "CICIoT sampled",
        "UNSW-NB15 official split": "UNSW",
        "NF-ToN-IoT NetFlow stress": "NF-ToN stress",
        "NF-BoT-IoT NetFlow stress": "NF-BoT stress",
        "NF-ToN-IoT NetFlow near-full": "NF-ToN cap",
        "NF-BoT-IoT NetFlow near-full": "NF-BoT cap",
        "UNSW-NB15 v0.5 calibrated": "v0.5",
        "UNSW-NB15 v0.6 calibrated gate": "v0.6",
        "UNSW-NB15 v0.7 calibration objective": "v0.7",
        "UNSW-NB15 v0.8 post-hoc calibration": "v0.8",
    }
    return replacements.get(evidence_block, evidence_block)


def add_boundary_notes(ax: plt.Axes, rows: list[dict[str, object]], y: float = -0.24) -> None:
    notes = []
    for row in rows:
        boundary = str(row.get("boundary", ""))
        if "not full" in boundary or "Bounded" in boundary or "cap" in boundary:
            notes.append(short_label(str(row["evidence_block"])) + ": bounded")
        elif "Neutral" in boundary or "not established" in boundary:
            notes.append(short_label(str(row["evidence_block"])) + ": neutral")
    if notes:
        ax.text(
            0,
            y,
            "; ".join(notes[:4]),
            transform=ax.transAxes,
            fontsize=7,
            color="#555555",
            va="top",
        )


def plot_panel_a(ax: plt.Axes, rows: list[dict[str, object]]) -> None:
    labels = [short_label(str(row["evidence_block"])) for row in rows]
    variants = ["traffic_only", "weak_cti", "source_gate", "random_cti"]
    x = np.arange(len(rows))
    width = 0.19
    offsets = np.linspace(-1.5 * width, 1.5 * width, len(variants))
    for offset, variant in zip(offsets, variants):
        values = [row[variant] if row[variant] is not None else np.nan for row in rows]
        ax.bar(
            x + offset,
            values,
            width,
            label=variant.replace("_", " "),
            color=VARIANT_COLORS[variant],
            edgecolor="white",
            linewidth=0.6,
        )
    ax.set_title("A. Cross-dataset Macro-F1", loc="left", fontweight="bold")
    ax.set_ylabel("Macro-F1")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha="right")
    ax.set_ylim(0, 0.9)
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.8)
    ax.legend(ncol=2, fontsize=7, frameon=False, loc="upper left")
    for idx, row in enumerate(rows):
        delta = row["source_delta_vs_weak"]
        if isinstance(delta, float) and delta < 0:
            source = row["source_gate"]
            if isinstance(source, float):
                ax.text(
                    idx + offsets[2],
                    max(source - 0.08, 0.05),
                    "trails weak",
                    ha="center",
                    va="center",
                    fontsize=5.7,
                    rotation=90,
                    color="white",
                    fontweight="bold",
                    clip_on=True,
                )
    add_boundary_notes(ax, rows)


def plot_panel_b(ax: plt.Axes, rows: list[dict[str, object]]) -> None:
    labels = [short_label(str(row["evidence_block"])) for row in rows]
    deltas = [float(row["source_delta_vs_traffic"]) for row in rows]
    colors = ["#56B4E9" if "stress" in label else "#009E73" for label in labels]
    y = np.arange(len(rows))
    ax.barh(y, deltas, color=colors, edgecolor="white", linewidth=0.6)
    ax.axvline(0, color="#333333", linewidth=0.8)
    ax.set_title("B. Source-gate gain on NetFlow", loc="left", fontweight="bold")
    ax.set_xlabel("Macro-F1 delta vs traffic-only")
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.grid(axis="x", color="#E6E6E6", linewidth=0.8)
    for yi, delta, label in zip(y, deltas, labels):
        ax.text(delta + 0.006, yi, f"+{delta:.3f}", va="center", fontsize=7)
        if "cap" in label:
            ax.text(0.002, yi - 0.27, "per-family cap", va="center", fontsize=6, color="#555555")
    ax.set_xlim(0, max(deltas) + 0.06)


def plot_panel_c(ax: plt.Axes, rows: list[dict[str, object]]) -> None:
    labels = [short_label(str(row["evidence_block"])) for row in rows]
    deltas = [float(row["source_delta_vs_traffic"]) for row in rows]
    x = np.arange(len(rows))
    ax.plot(x, deltas, marker="o", color="#009E73", linewidth=2)
    ax.fill_between(x, deltas, color="#009E73", alpha=0.15)
    ax.set_title("C. Calibration-aware gates preserve F1, not calibration", loc="left", fontweight="bold")
    ax.set_ylabel("Macro-F1 delta vs traffic-only")
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.8)
    ax.set_ylim(0, max(deltas) + 0.025)
    ax.text(
        0.02,
        0.88,
        "ECE/Brier remain unresolved",
        transform=ax.transAxes,
        fontsize=8,
        bbox=dict(facecolor="#FFF7D6", edgecolor="#E69F00", boxstyle="round,pad=0.25"),
    )


def plot_panel_d(ax: plt.Axes, rows: list[dict[str, object]]) -> None:
    row = rows[0]
    labels = ["traffic-only", "source gate", "random CTI"]
    values = [
        float(row["traffic_only"]),
        float(row["source_gate"]),
        float(row["random_cti"]),
    ]
    colors = [VARIANT_COLORS["traffic_only"], VARIANT_COLORS["source_gate"], VARIANT_COLORS["random_cti"]]
    x = np.arange(len(labels))
    ax.bar(x, values, color=colors, edgecolor="white", linewidth=0.6)
    ax.set_title("D. v0.8 ECE boundary", loc="left", fontweight="bold")
    ax.set_ylabel("Temperature-scaled ECE")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=10, ha="right")
    ax.grid(axis="y", color="#E6E6E6", linewidth=0.8)
    ymax = max(values) * 1.28
    ax.set_ylim(0, ymax)
    ax.text(
        1,
        values[1] + ymax * 0.04,
        "group3: 0.1067\nnot solved",
        ha="center",
        fontsize=7,
        color="#7A4B00",
    )


def build_figure(rows: list[dict[str, object]], title: str) -> plt.Figure:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8.5,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            "figure.dpi": 300,
            "savefig.dpi": 300,
        }
    )
    fig, axs = plt.subplots(2, 2, figsize=(11.6, 8.0), constrained_layout=True)
    plot_panel_a(axs[0, 0], require_rows(rows, "A"))
    plot_panel_b(axs[0, 1], require_rows(rows, "B"))
    plot_panel_c(axs[1, 0], require_rows(rows, "C"))
    plot_panel_d(axs[1, 1], require_rows(rows, "D"))
    fig.suptitle(title, fontsize=12, fontweight="bold", x=0.02, ha="left")
    fig.text(
        0.02,
        0.005,
        "Boundaries: CICIoT is sampled; NetFlow near-full is per-family capped; calibration remains unresolved; no P17 superiority claim.",
        fontsize=7,
        color="#444444",
    )
    return fig


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate TrustFedFusion-IDS Figure 4.")
    parser.add_argument("--input", type=Path, default=Path("05_Figures/figure4_cross_dataset_data.csv"))
    parser.add_argument("--output-prefix", type=Path, default=Path("05_Figures/figure4_publication_draft"))
    parser.add_argument("--title", default="Cross-dataset evidence and calibration boundary")
    args = parser.parse_args()

    rows = load_rows(args.input)
    fig = build_figure(rows, args.title)
    prefix = args.output_prefix
    prefix.parent.mkdir(parents=True, exist_ok=True)
    for ext in ["svg", "pdf", "png"]:
        output = prefix.with_suffix(f".{ext}")
        fig.savefig(output, bbox_inches="tight")
        if not output.exists() or output.stat().st_size <= 0:
            raise RuntimeError(f"Failed to write {output}")
    plt.close(fig)


if __name__ == "__main__":
    main()
