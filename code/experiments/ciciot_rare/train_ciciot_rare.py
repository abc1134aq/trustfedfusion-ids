#!/usr/bin/env python3
"""Kaggle-side rare-family CICIoT2023 cross-domain baseline for TrustFedFusion-IDS.

The script reads mounted Kaggle input files in bounded chunks, maps raw labels to
attack families, trains a lightweight NumPy softmax model, and writes traceable
metrics. It is intentionally storage-safe: it never copies the full dataset to
local project storage.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd


INPUT_ROOT = Path("/kaggle/input")
DEFAULT_OUT_DIR = Path("04_Results/ciciot2023_rare_sampled")
LABEL_LIKE_COLUMNS = {
    "attack_label",
    "attack_type",
    "label",
    "class",
    "category",
    "attack",
    "attack_cat",
    "_family_label",
}
CTI_SOURCE_RELIABILITY = {
    "tcp": 0.90,
    "udp": 0.75,
    "icmp": 0.70,
    "dns": 0.80,
    "http": 0.70,
    "arp": 0.65,
    "rate": 0.60,
    "flow": 0.60,
}
CANONICAL_FAMILIES = [
    "benign",
    "dos_ddos",
    "mirai",
    "recon",
    "spoofing_mitm",
    "brute_force",
    "web_injection",
    "malware",
    "other",
]


def normalize_label(text: object) -> str:
    return str(text).strip().lower().replace("_", "-").replace(" ", "")


def map_family(label: object) -> str:
    low = normalize_label(label)
    if not low or low in {"nan", "none"}:
        return "other"
    if "benign" in low or low == "normal":
        return "benign"
    if "ddos" in low or low.startswith("dos") or "flood" in low or "slowloris" in low:
        return "dos_ddos"
    if "mirai" in low:
        return "mirai"
    if "recon" in low or "scan" in low or "fingerprint" in low or "vulnerability" in low:
        return "recon"
    if "mitm" in low or "spoof" in low or "arpspoof" in low:
        return "spoofing_mitm"
    if "bruteforce" in low or "dictionary" in low or "password" in low:
        return "brute_force"
    if "sql" in low or "xss" in low or "commandinjection" in low or "injection" in low:
        return "web_injection"
    if "browserhijacking" in low or "upload" in low:
        return "web_injection"
    if "backdoor" in low or "ransom" in low or "malware" in low:
        return "malware"
    return "other"


def detect_label_col(columns: list[str], requested: str | None) -> str:
    if requested:
        if requested not in columns:
            raise ValueError(f"Requested label column not found: {requested}")
        return requested
    lowered = {col.lower(): col for col in columns}
    for candidate in ["label", "Label", "Attack_type", "Attack_Label", "class", "attack_cat"]:
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    for col in columns:
        low = col.lower()
        if "label" in low or "attack" in low or "class" in low:
            return col
    raise ValueError("No label column found.")


def find_input_files(data: str | None, max_files: int) -> list[Path]:
    if data:
        path = Path(data)
        if path.is_file():
            return [path]
        files = sorted(p for p in path.rglob("*.csv") if p.is_file())
        if files:
            return files[:max_files]
        raise FileNotFoundError(f"No CSV files found at {data}")
    if not INPUT_ROOT.exists():
        raise FileNotFoundError("Kaggle input root not found; pass --data for local smoke tests.")
    files = [
        p
        for p in INPUT_ROOT.rglob("*.csv")
        if p.is_file() and ("CICIoT2023" in str(p) or "ciciot" in str(p).lower())
    ]
    if not files:
        files = [p for p in INPUT_ROOT.rglob("*.csv") if p.is_file()]
    files.sort(key=lambda p: (str(p.parent), p.name))
    return files[:max_files]


def bounded_family_sample(
    files: list[Path],
    label_col: str | None,
    per_family: int,
    chunk_size: int,
    max_rows_read: int,
    seed: int,
) -> tuple[pd.DataFrame, dict[str, object]]:
    rng = np.random.default_rng(seed)
    kept: dict[str, list[pd.DataFrame]] = defaultdict(list)
    counts = {family: 0 for family in CANONICAL_FAMILIES}
    rows_read = 0
    file_summaries: list[dict[str, object]] = []
    resolved_label_col: str | None = None

    for file_index, path in enumerate(files, start=1):
        if rows_read >= max_rows_read:
            break
        file_rows = 0
        try:
            preview = pd.read_csv(path, nrows=5, low_memory=False)
            resolved_label_col = detect_label_col(preview.columns.astype(str).tolist(), label_col)
        except Exception as exc:
            file_summaries.append({"file": str(path), "status": "error", "error": repr(exc)})
            continue

        try:
            for chunk in pd.read_csv(path, chunksize=chunk_size, low_memory=False):
                if rows_read >= max_rows_read:
                    break
                chunk.columns = chunk.columns.astype(str)
                if resolved_label_col not in chunk.columns:
                    continue
                file_rows += len(chunk)
                rows_read += len(chunk)
                chunk = chunk.copy()
                chunk["_family_label"] = chunk[resolved_label_col].map(map_family)
                for family, group in chunk.groupby("_family_label", sort=False):
                    if family not in counts:
                        counts[family] = 0
                    need = per_family - counts[family]
                    if need <= 0:
                        continue
                    take = min(need, len(group))
                    if take <= 0:
                        continue
                    if len(group) > take:
                        group = group.sample(n=take, random_state=int(rng.integers(0, 1_000_000_000)))
                    kept[family].append(group)
                    counts[family] += int(len(group))
                if sum(counts.values()) >= per_family * max(1, len([c for c in counts.values() if c > 0])):
                    saturated_known = all(c >= per_family for c in counts.values() if c > 0)
                    if saturated_known and sum(c > 0 for c in counts.values()) >= 5:
                        break
        except Exception as exc:
            file_summaries.append(
                {
                    "file": str(path),
                    "status": "partial_error",
                    "rows_read": file_rows,
                    "error": repr(exc),
                }
            )
            continue

        file_summaries.append(
            {
                "file": str(path),
                "status": "ok",
                "rows_read": file_rows,
                "file_index": file_index,
            }
        )

    frames = [frame for family_frames in kept.values() for frame in family_frames]
    if not frames:
        raise RuntimeError("No sampled rows collected.")
    df = pd.concat(frames, axis=0, ignore_index=True)
    df = df.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    manifest = {
        "files": [str(p) for p in files],
        "file_summaries": file_summaries,
        "label_col": resolved_label_col,
        "rows_read_bounded": rows_read,
        "sample_rows": int(len(df)),
        "family_counts": {k: int(v) for k, v in df["_family_label"].value_counts().sort_index().items()},
        "per_family_cap": per_family,
        "max_rows_read": max_rows_read,
        "full_dataset_downloaded_locally": False,
    }
    return df, manifest


def numeric_col(df: pd.DataFrame, names: list[str]) -> pd.Series:
    for name in names:
        if name in df.columns:
            return pd.to_numeric(df[name], errors="coerce").fillna(0.0).astype(float)
    return pd.Series(np.zeros(len(df)), index=df.index, dtype=float)


def present_from_names(df: pd.DataFrame, names: list[str], prefixes: list[str]) -> pd.Series:
    present = pd.Series(False, index=df.index)
    for name in names:
        if name in df.columns:
            numeric = pd.to_numeric(df[name], errors="coerce").fillna(0.0).astype(float)
            text = df[name].astype(str).str.lower()
            present = present | (numeric.abs() > 1e-12) | ~text.isin({"", "0", "0.0", "nan", "none"})
    for prefix in prefixes:
        for col in [c for c in df.columns if c.lower().startswith(prefix.lower())]:
            numeric = pd.to_numeric(df[col], errors="coerce")
            text = df[col].astype(str).str.lower()
            present = present | (numeric.fillna(0.0).astype(float).abs() > 1e-12) | ~text.isin(
                {"", "0", "0.0", "nan", "none"}
            )
    return present.astype(float)


def high_quantile(series: pd.Series, q: float = 0.75) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0).astype(float)
    threshold = float(values.quantile(q))
    if threshold <= 0:
        return (values > 0).astype(float)
    return (values >= threshold).astype(float)


def add_cti_features(df: pd.DataFrame, mode: str, seed: int) -> tuple[pd.DataFrame, dict[str, object]]:
    if mode == "traffic_only":
        return df.copy(), {"cti_mode": mode, "cti_columns": []}

    rng = np.random.default_rng(seed)
    out = df.copy()
    hints: dict[str, tuple[pd.Series, str]] = {
        "_cti_tcp_present": (present_from_names(df, ["TCP"], ["tcp."]), "tcp"),
        "_cti_udp_present": (present_from_names(df, ["UDP"], ["udp."]), "udp"),
        "_cti_icmp_present": (present_from_names(df, ["ICMP"], ["icmp."]), "icmp"),
        "_cti_dns_present": (present_from_names(df, ["DNS"], ["dns."]), "dns"),
        "_cti_http_present": (present_from_names(df, ["HTTP", "HTTPS"], ["http."]), "http"),
        "_cti_arp_present": (present_from_names(df, ["ARP"], ["arp."]), "arp"),
        "_cti_rate_high": (high_quantile(numeric_col(df, ["Rate", "Srate", "Drate"])), "rate"),
        "_cti_flow_duration_high": (high_quantile(numeric_col(df, ["flow_duration", "Duration"])), "flow"),
        "_cti_syn_flag": (high_quantile(numeric_col(df, ["syn_flag_number", "syn_count", "tcp.connection.syn"])), "tcp"),
        "_cti_rst_flag": (high_quantile(numeric_col(df, ["rst_flag_number", "rst_count", "tcp.connection.rst"])), "tcp"),
        "_cti_header_high": (high_quantile(numeric_col(df, ["Header_Length", "Tot size", "tcp.len"])), "flow"),
    }

    cti_cols: list[str] = []
    source_cols: dict[str, str] = {}
    for col, (series, source) in hints.items():
        values = series.to_numpy(dtype=float)
        if mode == "random_cti":
            rng.shuffle(values)
        out[col] = values.astype(float)
        cti_cols.append(col)
        source_cols[col] = source

    if mode == "source_gate":
        hint_cols = list(source_cols.keys())
        source_gates: list[np.ndarray] = []
        for source, reliability in CTI_SOURCE_RELIABILITY.items():
            cols = [col for col in hint_cols if source_cols[col] == source]
            if not cols:
                continue
            active = np.zeros(len(out), dtype=float)
            for col in cols:
                active += (out[col].to_numpy(dtype=float) > 0).astype(float)
            saturation = max(1.0, min(3.0, float(len(cols))))
            gate = reliability * np.minimum(active / saturation, 1.0)
            active_col = f"_cti_{source}_active_count"
            gate_col = f"_cti_{source}_gate"
            out[active_col] = active.astype(float)
            out[gate_col] = gate.astype(float)
            cti_cols.extend([active_col, gate_col])
            source_gates.append(gate)
            for col in cols:
                gated_col = f"{col}_source_gate"
                out[gated_col] = out[col].to_numpy(dtype=float) * gate
                cti_cols.append(gated_col)
        if source_gates:
            stacked = np.stack(source_gates, axis=1)
            out["_cti_source_gate_mean"] = stacked.mean(axis=1).astype(float)
            out["_cti_source_gate_max"] = stacked.max(axis=1).astype(float)
        else:
            out["_cti_source_gate_mean"] = 0.0
            out["_cti_source_gate_max"] = 0.0
        cti_cols.extend(["_cti_source_gate_mean", "_cti_source_gate_max"])

    return out, {
        "cti_mode": mode,
        "cti_columns": cti_cols,
        "source_reliability": CTI_SOURCE_RELIABILITY,
        "leakage_guard": "CTI hints are generated from observable protocol/flow fields only, never from labels.",
    }


def build_features(df: pd.DataFrame, label_col: str) -> tuple[np.ndarray, np.ndarray, list[str], list[str], dict[str, int]]:
    labels = sorted(df[label_col].astype(str).unique().tolist())
    label_to_id = {label: i for i, label in enumerate(labels)}
    y = df[label_col].astype(str).map(label_to_id).to_numpy(dtype=np.int64)

    features: list[np.ndarray] = []
    used: list[str] = []
    skipped: list[str] = []
    for col in df.columns.astype(str):
        if col == label_col or col.lower() in LABEL_LIKE_COLUMNS:
            continue
        numeric = pd.to_numeric(df[col], errors="coerce")
        valid = float(numeric.notna().mean())
        if valid < 0.80:
            skipped.append(col)
            continue
        median = numeric.median()
        if pd.isna(median):
            median = 0.0
        values = numeric.replace([np.inf, -np.inf], np.nan).fillna(median).to_numpy(dtype=np.float64)
        if np.nanstd(values) < 1e-12:
            skipped.append(col)
            continue
        features.append(values.reshape(-1, 1))
        used.append(col)
    if not features:
        raise ValueError("No numeric features available after leakage guard.")
    x = np.concatenate(features, axis=1)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0).astype(np.float32)
    return x, y, labels, used, skipped, label_to_id


def stratified_split(y: np.ndarray, test_ratio: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train: list[int] = []
    test: list[int] = []
    for label in np.unique(y):
        idx = np.where(y == label)[0]
        rng.shuffle(idx)
        if len(idx) <= 2:
            train.extend(idx.tolist())
            continue
        n_test = max(1, int(round(len(idx) * test_ratio)))
        test.extend(idx[:n_test].tolist())
        train.extend(idx[n_test:].tolist())
    rng.shuffle(train)
    rng.shuffle(test)
    return np.array(train, dtype=np.int64), np.array(test, dtype=np.int64)


def standardize(x_train: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mean = x_train.mean(axis=0, keepdims=True)
    std = x_train.std(axis=0, keepdims=True)
    std[std < 1e-8] = 1.0
    return ((x_train - mean) / std).astype(np.float32), ((x_test - mean) / std).astype(np.float32)


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(logits)
    return exp / exp.sum(axis=1, keepdims=True)


def train_softmax(
    x: np.ndarray,
    y: np.ndarray,
    n_classes: int,
    epochs: int,
    batch_size: int,
    lr: float,
    seed: int,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    w = rng.normal(0.0, 0.01, size=(x.shape[1], n_classes)).astype(np.float32)
    b = np.zeros(n_classes, dtype=np.float32)
    class_counts = np.bincount(y, minlength=n_classes).astype(np.float64)
    class_weights = class_counts.sum() / np.maximum(class_counts, 1.0)
    class_weights = class_weights / class_weights.mean()
    for _ in range(epochs):
        idx = np.arange(len(y))
        rng.shuffle(idx)
        for start in range(0, len(idx), batch_size):
            batch = idx[start : start + batch_size]
            xb = x[batch]
            yb = y[batch]
            probs = softmax(xb @ w + b)
            weights = class_weights[yb].astype(np.float32)
            probs[np.arange(len(batch)), yb] -= 1.0
            probs *= weights[:, None]
            probs /= max(1, len(batch))
            grad_w = xb.T @ probs
            grad_b = probs.sum(axis=0)
            w -= lr * grad_w.astype(np.float32)
            b -= lr * grad_b.astype(np.float32)
    return {"w": w, "b": b}


def calibration_metrics(probs: np.ndarray, y: np.ndarray, n_classes: int, bins: int = 15) -> dict[str, float]:
    pred = probs.argmax(axis=1)
    confidence = probs.max(axis=1)
    correct = (pred == y).astype(np.float64)
    one_hot = np.eye(n_classes, dtype=np.float64)[y]
    brier = float(np.mean(np.sum((probs.astype(np.float64) - one_hot) ** 2, axis=1)))
    ece = 0.0
    edges = np.linspace(0.0, 1.0, bins + 1)
    for lower, upper in zip(edges[:-1], edges[1:]):
        if upper == 1.0:
            mask = (confidence >= lower) & (confidence <= upper)
        else:
            mask = (confidence >= lower) & (confidence < upper)
        if not np.any(mask):
            continue
        ece += float(mask.mean()) * abs(float(correct[mask].mean()) - float(confidence[mask].mean()))
    return {"ece": float(ece), "brier": brier, "mean_confidence": float(confidence.mean())}


def evaluate(x: np.ndarray, y: np.ndarray, labels: list[str], model: dict[str, np.ndarray]) -> dict[str, object]:
    start = time.perf_counter()
    probs = softmax(x @ model["w"] + model["b"])
    elapsed = time.perf_counter() - start
    pred = probs.argmax(axis=1)
    rows = []
    f1s: list[float] = []
    for i, label in enumerate(labels):
        tp = float(((pred == i) & (y == i)).sum())
        fp = float(((pred == i) & (y != i)).sum())
        fn = float(((pred != i) & (y == i)).sum())
        support = int((y == i).sum())
        precision = tp / (tp + fp + 1e-12)
        recall = tp / (tp + fn + 1e-12)
        f1 = 2 * precision * recall / (precision + recall + 1e-12)
        f1s.append(float(f1))
        rows.append(
            {
                "family": label,
                "precision": float(precision),
                "recall": float(recall),
                "f1": float(f1),
                "support": support,
            }
        )
    benign_ids = [i for i, label in enumerate(labels) if label == "benign"]
    fpr_normal = math.nan
    if benign_ids:
        benign_mask = y == benign_ids[0]
        if benign_mask.sum() > 0:
            fpr_normal = float((pred[benign_mask] != benign_ids[0]).mean())
    result: dict[str, object] = {
        "accuracy": float((pred == y).mean()),
        "macro_f1": float(np.mean(f1s)),
        "normal_fpr": fpr_normal,
        "inference_latency_ms_per_1k": float(elapsed * 1000.0 / max(1.0, len(y) / 1000.0)),
        "per_family": rows,
    }
    result.update(calibration_metrics(probs, y, len(labels)))
    return result


def write_scenario_outputs(out_dir: Path, name: str, metrics: dict[str, object], metadata: dict[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {**metadata, **metrics}
    (out_dir / f"{name}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    rows = metrics.get("per_family", [])
    with (out_dir / f"{name}_per_family.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["family", "precision", "recall", "f1", "support"])
        writer.writeheader()
        for row in rows if isinstance(rows, list) else []:
            writer.writerow(row)


def run_scenario(
    sampled: pd.DataFrame,
    sample_manifest: dict[str, object],
    mode: str,
    seed: int,
    args: argparse.Namespace,
) -> dict[str, object]:
    df_mode, cti_meta = add_cti_features(sampled, mode, seed)
    x, y, labels, used, skipped, label_to_id = build_features(df_mode, "_family_label")
    train_idx, test_idx = stratified_split(y, args.test_ratio, seed)
    x_train, x_test = standardize(x[train_idx], x[test_idx])
    y_train, y_test = y[train_idx], y[test_idx]
    model = train_softmax(
        x_train,
        y_train,
        len(labels),
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        seed=seed,
    )
    metrics = evaluate(x_test, y_test, labels, model)
    metadata = {
        "dataset_name": args.dataset_name,
        "scenario": mode,
        "seed": seed,
        "train_rows": int(len(train_idx)),
        "test_rows": int(len(test_idx)),
        "n_features": int(x.shape[1]),
        "labels": labels,
        "label_to_id": label_to_id,
        "used_features": used,
        "skipped_features": skipped,
        "cti_metadata": cti_meta,
        "sample_manifest_digest": {
            "sample_rows": sample_manifest["sample_rows"],
            "family_counts": sample_manifest["family_counts"],
            "rows_read_bounded": sample_manifest["rows_read_bounded"],
            "full_dataset_downloaded_locally": False,
        },
        "honesty_boundary": "This is a rare-family bounded sampled cross-domain probe, not a full-dataset final result.",
    }
    name = f"{args.dataset_name}_{mode}_seed{seed}"
    write_scenario_outputs(Path(args.out_dir), name, metrics, metadata)
    return {**metadata, **{k: v for k, v in metrics.items() if k != "per_family"}}


def write_summary(out_dir: Path, rows: list[dict[str, object]], sample_manifest: dict[str, object]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_cols = [
        "dataset_name",
        "scenario",
        "seed",
        "accuracy",
        "macro_f1",
        "normal_fpr",
        "ece",
        "brier",
        "mean_confidence",
        "inference_latency_ms_per_1k",
        "train_rows",
        "test_rows",
        "n_features",
    ]
    with (out_dir / "ciciot2023_rare_sampled_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in csv_cols})

    lines = [
        "# CICIoT2023 Rare-Family Sampled Cross-Domain Baseline",
        "",
        "This is a rare-family bounded Kaggle-side probe. It does not download the full dataset to local storage.",
        "",
        "## Sample",
        "",
        f"- Rows read under bound: {sample_manifest.get('rows_read_bounded')}",
        f"- Sample rows: {sample_manifest.get('sample_rows')}",
        f"- Family counts: `{json.dumps(sample_manifest.get('family_counts', {}), ensure_ascii=False)}`",
        "",
        "## Metrics",
        "",
        "| Scenario | Seed | Macro-F1 | Accuracy | Normal FPR | ECE | Brier | Latency ms / 1k |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('scenario')} | {row.get('seed')} | {float(row.get('macro_f1', math.nan)):.4f} | "
            f"{float(row.get('accuracy', math.nan)):.4f} | {float(row.get('normal_fpr', math.nan)):.4f} | "
            f"{float(row.get('ece', math.nan)):.4f} | {float(row.get('brier', math.nan)):.4f} | "
            f"{float(row.get('inference_latency_ms_per_1k', math.nan)):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Interpretation Guard",
            "",
            "- Treat these numbers as rare-family sampled cross-domain feasibility evidence only.",
            "- Random CTI is the negative control; if it improves, the CTI feature design must be rechecked.",
            "- Source-gate gains must be confirmed on Edge-IIoT and CICIoT with repeated seeds before manuscript claims.",
        ]
    )
    (out_dir / "ciciot2023_rare_sampled_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=None, help="Optional local file or directory for smoke tests.")
    parser.add_argument("--label-col", default=None)
    parser.add_argument("--dataset-name", default="ciciot2023_rare_sampled")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--per-family", type=int, default=3000)
    parser.add_argument("--max-files", type=int, default=120)
    parser.add_argument("--chunk-size", type=int, default=50000)
    parser.add_argument("--max-rows-read", type=int, default=8_000_000)
    parser.add_argument("--test-ratio", type=float, default=0.25)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["traffic_only", "weak_cti_concat", "source_gate", "random_cti"],
        choices=["traffic_only", "weak_cti", "weak_cti_concat", "source_gate", "random_cti"],
    )
    return parser.parse_args()


def main() -> None:
    started = time.time()
    args = parse_args()
    out_dir = Path(args.out_dir)
    files = find_input_files(args.data, args.max_files)
    sampled, sample_manifest = bounded_family_sample(
        files=files,
        label_col=args.label_col,
        per_family=args.per_family,
        chunk_size=args.chunk_size,
        max_rows_read=args.max_rows_read,
        seed=args.seeds[0],
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    sample_manifest["elapsed_sampling_seconds"] = round(time.time() - started, 3)
    (out_dir / "ciciot2023_rare_sample_manifest.json").write_text(
        json.dumps(sample_manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    summary_rows: list[dict[str, object]] = []
    for seed in args.seeds:
        for mode in args.modes:
            scenario_mode = "weak_cti_concat" if mode == "weak_cti" else mode
            print(f"RUN mode={scenario_mode} seed={seed}")
            summary_rows.append(run_scenario(sampled, sample_manifest, scenario_mode, seed, args))
    write_summary(out_dir, summary_rows, sample_manifest)
    print(f"wrote {out_dir}")


if __name__ == "__main__":
    main()
