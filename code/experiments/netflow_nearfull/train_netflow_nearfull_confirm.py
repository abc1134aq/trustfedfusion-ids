#!/usr/bin/env python3
"""NF-ToN/NF-BoT near-full confirmation for TrustFedFusion-IDS."""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


INPUT_ROOT = Path("/kaggle/input")
DEFAULT_OUT_DIR = Path("04_Results/netflow_nearfull_confirm")
LABEL_COL = "Attack"
LABEL_LIKE = {"label", "attack", "class", "_family_label"}
EXCLUDE_SUBSTRINGS = ["IPV4_SRC_ADDR", "IPV4_DST_ADDR", "IPV6", "SRC_ADDR", "DST_ADDR"]
CTI_SOURCE_RELIABILITY = {
    "tcp": 0.90,
    "udp": 0.75,
    "icmp": 0.70,
    "bytes": 0.60,
    "packets": 0.60,
    "duration": 0.60,
    "flags": 0.70,
    "ports": 0.65,
}


DATASETS = {
    "nf_ton_iot": "NF-ToN-IoT.parquet",
    "nf_bot_iot": "NF-BoT-IoT.parquet",
}


def normalize_label(value: object) -> str:
    text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if text in {"benign", "normal"}:
        return "benign"
    if text in {"ddos", "dos", "reconnaissance", "theft", "injection", "password", "xss", "scanning", "backdoor", "mitm", "ransomware"}:
        return text
    if "scan" in text or "recon" in text:
        return "reconnaissance"
    if "ddos" in text:
        return "ddos"
    if text.startswith("dos"):
        return "dos"
    return text or "unknown"


def find_file(filename: str, explicit_root: str | None) -> Path:
    if explicit_root:
        root = Path(explicit_root)
        direct = root / filename
        if direct.exists():
            return direct
        matches = sorted(root.rglob(filename))
        if matches:
            return matches[0]
    local_roots = [Path("02_Data/kaggle/nf_ton_iot"), Path("02_Data/kaggle/nf_bot_iot")]
    for root in local_roots:
        path = root / filename
        if path.exists():
            return path
    if INPUT_ROOT.exists():
        matches = sorted(INPUT_ROOT.rglob(filename))
        if matches:
            return matches[0]
    raise FileNotFoundError(filename)


def read_sample(path: Path, per_family: int, seed: int) -> tuple[pd.DataFrame, dict[str, Any]]:
    df = pd.read_parquet(path) if path.suffix.lower() == ".parquet" else pd.read_csv(path, low_memory=False)
    df.columns = df.columns.astype(str)
    if LABEL_COL not in df.columns:
        raise ValueError(f"{path} does not contain {LABEL_COL}; columns={df.columns.tolist()}")
    df = df.copy()
    df["_family_label"] = df[LABEL_COL].map(normalize_label)
    rng = np.random.default_rng(seed)
    frames: list[pd.DataFrame] = []
    counts: dict[str, int] = {}
    for family, group in df.groupby("_family_label", sort=True):
        take = min(per_family, len(group))
        if len(group) > take:
            group = group.sample(n=take, random_state=int(rng.integers(0, 1_000_000_000)))
        frames.append(group)
        counts[str(family)] = int(len(group))
    sampled = pd.concat(frames, axis=0, ignore_index=True)
    sampled = sampled.sample(frac=1.0, random_state=seed).reset_index(drop=True)
    manifest = {
        "path": str(path),
        "rows_available": int(len(df)),
        "rows_sampled": int(len(sampled)),
        "per_family_cap": int(per_family),
        "family_counts_available": {str(k): int(v) for k, v in df["_family_label"].value_counts().sort_index().items()},
        "family_counts_sampled": counts,
        "full_dataset_downloaded_locally": False,
    }
    return sampled, manifest


def numeric(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(np.zeros(len(df)), index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0).astype(float)


def high(train: pd.Series, values: pd.Series, q: float = 0.75) -> pd.Series:
    train = pd.to_numeric(train, errors="coerce").fillna(0.0).astype(float)
    values = pd.to_numeric(values, errors="coerce").fillna(0.0).astype(float)
    threshold = float(train.quantile(q))
    if threshold <= 0:
        return (values > 0).astype(float)
    return (values >= threshold).astype(float)


def add_cti(train: pd.DataFrame, test: pd.DataFrame, mode: str, seed: int) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if mode == "traffic_only":
        return train.copy(), test.copy(), {"cti_mode": mode, "cti_columns": []}
    rng = np.random.default_rng(seed)
    train_out = train.copy()
    test_out = test.copy()
    proto_train = numeric(train, "PROTOCOL")
    proto_test = numeric(test, "PROTOCOL")
    specs: list[tuple[str, pd.Series, pd.Series, str]] = [
        ("_cti_proto_tcp", (proto_train == 6).astype(float), (proto_test == 6).astype(float), "tcp"),
        ("_cti_proto_udp", (proto_train == 17).astype(float), (proto_test == 17).astype(float), "udp"),
        ("_cti_proto_icmp", (proto_train == 1).astype(float), (proto_test == 1).astype(float), "icmp"),
        ("_cti_in_bytes_high", high(numeric(train, "IN_BYTES"), numeric(train, "IN_BYTES")), high(numeric(train, "IN_BYTES"), numeric(test, "IN_BYTES")), "bytes"),
        ("_cti_out_bytes_high", high(numeric(train, "OUT_BYTES"), numeric(train, "OUT_BYTES")), high(numeric(train, "OUT_BYTES"), numeric(test, "OUT_BYTES")), "bytes"),
        ("_cti_in_pkts_high", high(numeric(train, "IN_PKTS"), numeric(train, "IN_PKTS")), high(numeric(train, "IN_PKTS"), numeric(test, "IN_PKTS")), "packets"),
        ("_cti_out_pkts_high", high(numeric(train, "OUT_PKTS"), numeric(train, "OUT_PKTS")), high(numeric(train, "OUT_PKTS"), numeric(test, "OUT_PKTS")), "packets"),
        ("_cti_duration_high", high(numeric(train, "FLOW_DURATION_MILLISECONDS"), numeric(train, "FLOW_DURATION_MILLISECONDS")), high(numeric(train, "FLOW_DURATION_MILLISECONDS"), numeric(test, "FLOW_DURATION_MILLISECONDS")), "duration"),
        ("_cti_tcp_flags_high", high(numeric(train, "TCP_FLAGS"), numeric(train, "TCP_FLAGS")), high(numeric(train, "TCP_FLAGS"), numeric(test, "TCP_FLAGS")), "flags"),
        ("_cti_src_port_low", (numeric(train, "L4_SRC_PORT") < 1024).astype(float), (numeric(test, "L4_SRC_PORT") < 1024).astype(float), "ports"),
        ("_cti_dst_port_low", (numeric(train, "L4_DST_PORT") < 1024).astype(float), (numeric(test, "L4_DST_PORT") < 1024).astype(float), "ports"),
    ]
    cti_cols: list[str] = []
    source_for: dict[str, str] = {}
    for col, tr, te, source in specs:
        tr_arr = tr.to_numpy(dtype=float)
        te_arr = te.to_numpy(dtype=float)
        if mode == "random_cti":
            rng.shuffle(tr_arr)
            rng.shuffle(te_arr)
        train_out[col] = tr_arr.astype(float)
        test_out[col] = te_arr.astype(float)
        cti_cols.append(col)
        source_for[col] = source
    if mode == "source_gate":
        for frame in [train_out, test_out]:
            gates: list[np.ndarray] = []
            for source, reliability in CTI_SOURCE_RELIABILITY.items():
                cols = [col for col in cti_cols if source_for[col] == source]
                if not cols:
                    continue
                active = np.zeros(len(frame), dtype=float)
                for col in cols:
                    active += (frame[col].to_numpy(dtype=float) > 0).astype(float)
                saturation = max(1.0, min(3.0, float(len(cols))))
                gate = reliability * np.minimum(active / saturation, 1.0)
                frame[f"_cti_{source}_active_count"] = active.astype(float)
                frame[f"_cti_{source}_gate"] = gate.astype(float)
                gates.append(gate)
                for col in cols:
                    frame[f"{col}_source_gate"] = frame[col].to_numpy(dtype=float) * gate
            if gates:
                stacked = np.stack(gates, axis=1)
                frame["_cti_source_gate_mean"] = stacked.mean(axis=1).astype(float)
                frame["_cti_source_gate_max"] = stacked.max(axis=1).astype(float)
            else:
                frame["_cti_source_gate_mean"] = 0.0
                frame["_cti_source_gate_max"] = 0.0
        cti_cols = [col for col in train_out.columns if col.startswith("_cti_")]
    return train_out, test_out, {
        "cti_mode": mode,
        "cti_columns": cti_cols,
        "source_reliability": CTI_SOURCE_RELIABILITY,
        "leakage_guard": "NetFlow CTI hints use only protocol/ports/bytes/packets/duration/flags, not labels.",
    }


def split(df: pd.DataFrame, test_ratio: float, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    train_idx: list[int] = []
    test_idx: list[int] = []
    for _, group in df.groupby("_family_label", sort=True):
        idx = group.index.to_numpy()
        rng.shuffle(idx)
        n_test = max(1, int(round(len(idx) * test_ratio))) if len(idx) > 2 else 0
        test_idx.extend(idx[:n_test].tolist())
        train_idx.extend(idx[n_test:].tolist())
    rng.shuffle(train_idx)
    rng.shuffle(test_idx)
    return df.loc[train_idx].reset_index(drop=True), df.loc[test_idx].reset_index(drop=True)


def feature_columns(df: pd.DataFrame) -> list[str]:
    cols: list[str] = []
    for col in df.columns.astype(str):
        if col.lower() in LABEL_LIKE or col in LABEL_LIKE:
            continue
        if any(part.lower() in col.lower() for part in EXCLUDE_SUBSTRINGS):
            continue
        vals = pd.to_numeric(df[col], errors="coerce")
        if float(vals.notna().mean()) >= 0.90 and float(vals.fillna(0.0).std()) > 1e-12:
            cols.append(col)
    return cols


def transform(train: pd.DataFrame, test: pd.DataFrame, cols: list[str]) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
    xtr: list[np.ndarray] = []
    xte: list[np.ndarray] = []
    stats: dict[str, Any] = {}
    for col in cols:
        tr = pd.to_numeric(train[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        te = pd.to_numeric(test[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        median = float(tr.median()) if not pd.isna(tr.median()) else 0.0
        trv = tr.fillna(median).to_numpy(dtype=np.float64)
        tev = te.fillna(median).to_numpy(dtype=np.float64)
        mean = float(trv.mean())
        std = float(trv.std())
        if std < 1e-8:
            std = 1.0
        xtr.append(((trv - mean) / std).reshape(-1, 1))
        xte.append(((tev - mean) / std).reshape(-1, 1))
        stats[col] = {"median": median, "mean": mean, "std": std}
    return np.concatenate(xtr, axis=1).astype(np.float32), np.concatenate(xte, axis=1).astype(np.float32), stats


def encode(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str], dict[str, int]]:
    labels = sorted(train["_family_label"].astype(str).unique().tolist())
    label_to_id = {label: i for i, label in enumerate(labels)}
    ytr = train["_family_label"].astype(str).map(label_to_id).to_numpy(dtype=np.int64)
    yte = test["_family_label"].astype(str).map(label_to_id).fillna(-1).to_numpy(dtype=np.int64)
    if (yte < 0).any():
        raise ValueError("Test label missing from train labels.")
    return ytr, yte, labels, label_to_id


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(logits)
    return exp / exp.sum(axis=1, keepdims=True)


def train_model(x: np.ndarray, y: np.ndarray, n_classes: int, epochs: int, batch_size: int, lr: float, seed: int) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    w = rng.normal(0, 0.01, size=(x.shape[1], n_classes)).astype(np.float32)
    b = np.zeros(n_classes, dtype=np.float32)
    counts = np.bincount(y, minlength=n_classes).astype(np.float64)
    class_weights = counts.sum() / np.maximum(counts, 1)
    class_weights = class_weights / max(class_weights.mean(), 1e-12)
    for _ in range(epochs):
        idx = np.arange(len(y))
        rng.shuffle(idx)
        for start in range(0, len(idx), batch_size):
            batch = idx[start : start + batch_size]
            xb = x[batch]
            yb = y[batch]
            probs = softmax(xb @ w + b)
            probs[np.arange(len(batch)), yb] -= 1.0
            probs *= class_weights[yb].astype(np.float32)[:, None]
            probs /= max(1, len(batch))
            w -= lr * (xb.T @ probs).astype(np.float32)
            b -= lr * probs.sum(axis=0).astype(np.float32)
    return {"w": w, "b": b}


def calibration(probs: np.ndarray, y: np.ndarray, n_classes: int) -> dict[str, float]:
    pred = probs.argmax(axis=1)
    conf = probs.max(axis=1)
    correct = (pred == y).astype(np.float64)
    onehot = np.eye(n_classes, dtype=np.float64)[y]
    brier = float(np.mean(np.sum((probs.astype(np.float64) - onehot) ** 2, axis=1)))
    ece = 0.0
    edges = np.linspace(0, 1, 16)
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (conf >= lo) & (conf <= hi if hi == 1 else conf < hi)
        if np.any(mask):
            ece += float(mask.mean()) * abs(float(correct[mask].mean()) - float(conf[mask].mean()))
    return {"ece": ece, "brier": brier, "mean_confidence": float(conf.mean())}


def evaluate(x: np.ndarray, y: np.ndarray, labels: list[str], model: dict[str, np.ndarray]) -> dict[str, Any]:
    started = time.perf_counter()
    probs = softmax(x @ model["w"] + model["b"])
    elapsed = time.perf_counter() - started
    pred = probs.argmax(axis=1)
    per_family: list[dict[str, Any]] = []
    f1s: list[float] = []
    for i, label in enumerate(labels):
        tp = float(((pred == i) & (y == i)).sum())
        fp = float(((pred == i) & (y != i)).sum())
        fn = float(((pred != i) & (y == i)).sum())
        precision = tp / (tp + fp + 1e-12)
        recall = tp / (tp + fn + 1e-12)
        f1 = 2 * precision * recall / (precision + recall + 1e-12)
        f1s.append(f1)
        per_family.append({"family": label, "precision": precision, "recall": recall, "f1": f1, "support": int((y == i).sum())})
    benign_id = labels.index("benign") if "benign" in labels else None
    fpr = math.nan
    if benign_id is not None:
        mask = y == benign_id
        if mask.sum() > 0:
            fpr = float((pred[mask] != benign_id).mean())
    out: dict[str, Any] = {
        "accuracy": float((pred == y).mean()),
        "macro_f1": float(np.mean(f1s)),
        "normal_fpr": fpr,
        "inference_latency_ms_per_1k": float(elapsed * 1000 / max(1.0, len(y) / 1000.0)),
        "per_family": per_family,
    }
    out.update(calibration(probs, y, len(labels)))
    return out


def run_dataset(dataset: str, path: Path, args: argparse.Namespace) -> list[dict[str, Any]]:
    sampled, sample_manifest = read_sample(path, args.per_family, args.seeds[0])
    rows: list[dict[str, Any]] = []
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{dataset}_sample_manifest.json").write_text(json.dumps(sample_manifest, indent=2), encoding="utf-8")
    for seed in args.seeds:
        train_base, test_base = split(sampled, args.test_ratio, seed)
        for mode in args.modes:
            train_df, test_df, cti_meta = add_cti(train_base, test_base, mode, seed)
            cols = feature_columns(train_df)
            xtr, xte, stats = transform(train_df, test_df, cols)
            ytr, yte, labels, label_to_id = encode(train_df, test_df)
            model = train_model(xtr, ytr, len(labels), args.epochs, args.batch_size, args.lr, seed)
            metrics = evaluate(xte, yte, labels, model)
            row = {
                "dataset": dataset,
                "scenario": mode,
                "seed": seed,
                "train_rows": int(len(ytr)),
                "test_rows": int(len(yte)),
                "n_features": int(xtr.shape[1]),
                "accuracy": metrics["accuracy"],
                "macro_f1": metrics["macro_f1"],
                "normal_fpr": metrics["normal_fpr"],
                "ece": metrics["ece"],
                "brier": metrics["brier"],
                "mean_confidence": metrics["mean_confidence"],
                "inference_latency_ms_per_1k": metrics["inference_latency_ms_per_1k"],
            }
            rows.append(row)
            stem = f"{dataset}_{mode}_seed{seed}"
            payload = {
                "dataset": dataset,
                "scenario": mode,
                "seed": seed,
                "labels": labels,
                "label_to_id": label_to_id,
                "feature_columns": cols,
                "feature_stats": stats,
                "cti_metadata": cti_meta,
                "sample_manifest_digest": sample_manifest,
                "metrics": metrics,
                "honesty_boundary": "Near-full per-family-capped NetFlow confirmation; rare families may still be fully included while large families are capped.",
            }
            (out_dir / f"{stem}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            with (out_dir / f"{stem}_per_family.csv").open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["family", "precision", "recall", "f1", "support"])
                writer.writeheader()
                writer.writerows(metrics["per_family"])
            print(f"dataset={dataset} scenario={mode} seed={seed} macro_f1={row['macro_f1']:.4f} acc={row['accuracy']:.4f}")
    return rows


def write_summary(rows: list[dict[str, Any]], out_dir: Path) -> None:
    cols = ["dataset", "scenario", "seed", "accuracy", "macro_f1", "normal_fpr", "ece", "brier", "mean_confidence", "inference_latency_ms_per_1k", "train_rows", "test_rows", "n_features"]
    with (out_dir / "netflow_nearfull_confirm_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in cols})
    lines = [
        "# NF-ToN/NF-BoT NetFlow Near-Full Confirmation",
        "",
        "Near-full per-family-capped confirmation; not a claim of full raw-dataset training where large families exceed the cap.",
        "",
        "| Dataset | Scenario | Seed | Macro-F1 | Accuracy | Normal FPR | ECE | Brier |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(f"| {row['dataset']} | {row['scenario']} | {row['seed']} | {row['macro_f1']:.4f} | {row['accuracy']:.4f} | {row['normal_fpr']:.4f} | {row['ece']:.4f} | {row['brier']:.4f} |")
    (out_dir / "netflow_nearfull_confirm_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--per-family", type=int, default=100000)
    parser.add_argument("--test-ratio", type=float, default=0.25)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=4096)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--modes", nargs="+", default=["traffic_only", "weak_cti_concat", "source_gate", "random_cti"], choices=["traffic_only", "weak_cti_concat", "source_gate", "random_cti"])
    parser.add_argument("--datasets", nargs="+", default=["nf_ton_iot", "nf_bot_iot"], choices=list(DATASETS))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    all_rows: list[dict[str, Any]] = []
    for dataset in args.datasets:
        path = find_file(DATASETS[dataset], args.data_root)
        all_rows.extend(run_dataset(dataset, path, args))
    write_summary(all_rows, Path(args.out_dir))


if __name__ == "__main__":
    main()
