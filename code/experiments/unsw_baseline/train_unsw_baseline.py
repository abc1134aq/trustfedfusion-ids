#!/usr/bin/env python3
"""UNSW-NB15 bounded cross-domain baseline for TrustFedFusion-IDS.

The script uses the official train/test split, compares traffic-only features
with weak protocol/CTI hints, and keeps random CTI as a negative control.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


INPUT_ROOT = Path("/kaggle/input")
DEFAULT_OUT_DIR = Path("04_Results/unsw_nb15_baseline")
LABEL_COL = "attack_cat"
LABEL_LIKE = {"attack_cat", "label", "attack", "class", "_family_label"}
LOW_CARD_CAT = ["proto", "service", "state"]
CTI_SOURCE_RELIABILITY = {
    "tcp": 0.90,
    "udp": 0.75,
    "service": 0.70,
    "rate": 0.60,
    "flow": 0.60,
    "tcp_state": 0.70,
}


def normalize_label(value: object) -> str:
    text = str(value).strip().lower().replace(" ", "_").replace("-", "_")
    if text in {"normal", "benign"}:
        return "benign"
    if text in {"dos", "generic", "exploits", "fuzzers", "analysis", "backdoor", "shellcode", "worms", "reconnaissance"}:
        return text
    return text or "unknown"


def find_parquet(name: str, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise FileNotFoundError(path)
        return path
    candidates = [
        Path(f"02_Data/kaggle/unsw_nb15/{name}"),
        INPUT_ROOT / "unswnb15" / name,
    ]
    if INPUT_ROOT.exists():
        candidates.extend(sorted(INPUT_ROOT.rglob(name)))
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"Could not find {name}; pass explicit --train-data/--test-data.")


def read_table(path: Path, sample_rows: int, seed: int) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet":
        df = pd.read_parquet(path)
    else:
        df = pd.read_csv(path, low_memory=False)
    if sample_rows and sample_rows > 0 and sample_rows < len(df):
        df = df.sample(n=sample_rows, random_state=seed).reset_index(drop=True)
    df.columns = df.columns.astype(str)
    if LABEL_COL not in df.columns:
        raise ValueError(f"Expected label column {LABEL_COL}, got {df.columns.tolist()}")
    df = df.copy()
    df["_family_label"] = df[LABEL_COL].map(normalize_label)
    return df


def numeric_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series(np.zeros(len(df)), index=df.index, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0).astype(float)


def high_from_train(train_values: pd.Series, values: pd.Series, q: float = 0.75) -> pd.Series:
    train_values = pd.to_numeric(train_values, errors="coerce").fillna(0.0).astype(float)
    values = pd.to_numeric(values, errors="coerce").fillna(0.0).astype(float)
    threshold = float(train_values.quantile(q))
    if threshold <= 0:
        return (values > 0).astype(float)
    return (values >= threshold).astype(float)


def cti_feature_frames(
    train: pd.DataFrame,
    test: pd.DataFrame,
    mode: str,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if mode == "traffic_only":
        return train.copy(), test.copy(), {"cti_mode": mode, "cti_columns": []}

    rng = np.random.default_rng(seed)
    train_out = train.copy()
    test_out = test.copy()
    specs: list[tuple[str, pd.Series, pd.Series, str]] = [
        ("_cti_proto_tcp", (train["proto"].astype(str).str.lower() == "tcp").astype(float), (test["proto"].astype(str).str.lower() == "tcp").astype(float), "tcp"),
        ("_cti_proto_udp", (train["proto"].astype(str).str.lower() == "udp").astype(float), (test["proto"].astype(str).str.lower() == "udp").astype(float), "udp"),
        ("_cti_service_http", train["service"].astype(str).str.lower().isin({"http", "ssl", "ftp", "ftp-data"}).astype(float), test["service"].astype(str).str.lower().isin({"http", "ssl", "ftp", "ftp-data"}).astype(float), "service"),
        ("_cti_service_dns", train["service"].astype(str).str.lower().isin({"dns"}).astype(float), test["service"].astype(str).str.lower().isin({"dns"}).astype(float), "service"),
        ("_cti_state_int", (train["state"].astype(str).str.upper() == "INT").astype(float), (test["state"].astype(str).str.upper() == "INT").astype(float), "tcp_state"),
        ("_cti_state_fin", (train["state"].astype(str).str.upper() == "FIN").astype(float), (test["state"].astype(str).str.upper() == "FIN").astype(float), "tcp_state"),
        ("_cti_rate_high", high_from_train(numeric_series(train, "rate"), numeric_series(train, "rate")), high_from_train(numeric_series(train, "rate"), numeric_series(test, "rate")), "rate"),
        ("_cti_sload_high", high_from_train(numeric_series(train, "sload"), numeric_series(train, "sload")), high_from_train(numeric_series(train, "sload"), numeric_series(test, "sload")), "rate"),
        ("_cti_dload_high", high_from_train(numeric_series(train, "dload"), numeric_series(train, "dload")), high_from_train(numeric_series(train, "dload"), numeric_series(test, "dload")), "rate"),
        ("_cti_sbytes_high", high_from_train(numeric_series(train, "sbytes"), numeric_series(train, "sbytes")), high_from_train(numeric_series(train, "sbytes"), numeric_series(test, "sbytes")), "flow"),
        ("_cti_dbytes_high", high_from_train(numeric_series(train, "dbytes"), numeric_series(train, "dbytes")), high_from_train(numeric_series(train, "dbytes"), numeric_series(test, "dbytes")), "flow"),
        ("_cti_tcprtt_high", high_from_train(numeric_series(train, "tcprtt"), numeric_series(train, "tcprtt")), high_from_train(numeric_series(train, "tcprtt"), numeric_series(test, "tcprtt")), "tcp"),
    ]

    cti_cols: list[str] = []
    sources: dict[str, str] = {}
    for col, train_values, test_values, source in specs:
        train_arr = train_values.to_numpy(dtype=float)
        test_arr = test_values.to_numpy(dtype=float)
        if mode == "random_cti":
            rng.shuffle(train_arr)
            rng.shuffle(test_arr)
        train_out[col] = train_arr.astype(float)
        test_out[col] = test_arr.astype(float)
        cti_cols.append(col)
        sources[col] = source

    if mode == "source_gate":
        for frame in [train_out, test_out]:
            source_gates: list[np.ndarray] = []
            for source, reliability in CTI_SOURCE_RELIABILITY.items():
                cols = [col for col in cti_cols if sources[col] == source]
                if not cols:
                    continue
                active = np.zeros(len(frame), dtype=float)
                for col in cols:
                    active += (frame[col].to_numpy(dtype=float) > 0).astype(float)
                saturation = max(1.0, min(3.0, float(len(cols))))
                gate = reliability * np.minimum(active / saturation, 1.0)
                frame[f"_cti_{source}_active_count"] = active.astype(float)
                frame[f"_cti_{source}_gate"] = gate.astype(float)
                source_gates.append(gate)
                for col in cols:
                    frame[f"{col}_source_gate"] = frame[col].to_numpy(dtype=float) * gate
            if source_gates:
                stacked = np.stack(source_gates, axis=1)
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
        "leakage_guard": "Weak CTI hints use only UNSW flow/protocol/service/state fields, never attack_cat or label.",
    }


def fit_feature_spec(train: pd.DataFrame, max_cat_unique: int) -> dict[str, Any]:
    numeric_cols: list[str] = []
    categorical: dict[str, list[str]] = {}
    for col in train.columns.astype(str):
        if col in LABEL_LIKE or col.lower() in LABEL_LIKE:
            continue
        series = train[col]
        numeric = pd.to_numeric(series, errors="coerce")
        if float(numeric.notna().mean()) >= 0.90:
            if float(numeric.fillna(0.0).std()) > 1e-12:
                numeric_cols.append(col)
            continue
        if col in LOW_CARD_CAT or int(series.astype(str).nunique(dropna=True)) <= max_cat_unique:
            values = sorted(series.astype(str).fillna("MISSING").unique().tolist())
            if 1 < len(values) <= max_cat_unique:
                categorical[col] = values
    return {"numeric_cols": numeric_cols, "categorical": categorical}


def transform_features(df: pd.DataFrame, spec: dict[str, Any], train_stats: dict[str, Any] | None = None) -> tuple[np.ndarray, dict[str, Any], list[str]]:
    parts: list[np.ndarray] = []
    names: list[str] = []
    stats = {} if train_stats is None else train_stats
    for col in spec["numeric_cols"]:
        values = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        if train_stats is None:
            median = float(values.median()) if not pd.isna(values.median()) else 0.0
            filled = values.fillna(median).to_numpy(dtype=np.float64)
            mean = float(np.mean(filled))
            std = float(np.std(filled))
            if std < 1e-8:
                std = 1.0
            stats[col] = {"median": median, "mean": mean, "std": std}
        st = stats[col]
        arr = values.fillna(st["median"]).to_numpy(dtype=np.float64)
        arr = (arr - st["mean"]) / st["std"]
        parts.append(arr.reshape(-1, 1))
        names.append(col)
    for col, cats in spec["categorical"].items():
        text = df[col].astype(str).fillna("MISSING")
        for cat in cats:
            parts.append((text == cat).astype(float).to_numpy(dtype=np.float32).reshape(-1, 1))
            names.append(f"{col}={cat}")
    if not parts:
        raise ValueError("No features built.")
    x = np.concatenate(parts, axis=1).astype(np.float32)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    return x, stats, names


def encode_labels(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str], dict[str, int]]:
    labels = sorted(train["_family_label"].astype(str).unique().tolist())
    label_to_id = {label: i for i, label in enumerate(labels)}
    y_train = train["_family_label"].astype(str).map(label_to_id).to_numpy(dtype=np.int64)
    y_test = test["_family_label"].astype(str).map(label_to_id).fillna(-1).to_numpy(dtype=np.int64)
    keep = y_test >= 0
    if not np.all(keep):
        raise ValueError("Test set contains labels not present in train set.")
    return y_train, y_test, labels, label_to_id


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
    weight_decay: float,
    seed: int,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    w = rng.normal(0.0, 0.01, size=(x.shape[1], n_classes)).astype(np.float32)
    b = np.zeros(n_classes, dtype=np.float32)
    counts = np.bincount(y, minlength=n_classes).astype(np.float64)
    class_weights = counts.sum() / np.maximum(counts, 1.0)
    class_weights = class_weights / max(class_weights.mean(), 1e-12)
    for _ in range(epochs):
        idx = np.arange(len(y))
        rng.shuffle(idx)
        for start in range(0, len(idx), batch_size):
            batch = idx[start : start + batch_size]
            xb = x[batch]
            yb = y[batch]
            probs = softmax(xb @ w + b)
            row_weights = class_weights[yb].astype(np.float32)
            probs[np.arange(len(batch)), yb] -= 1.0
            probs *= row_weights[:, None]
            probs /= max(1, len(batch))
            grad_w = xb.T @ probs + weight_decay * w
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
        if np.any(mask):
            ece += float(mask.mean()) * abs(float(correct[mask].mean()) - float(confidence[mask].mean()))
    return {"ece": float(ece), "brier": brier, "mean_confidence": float(confidence.mean())}


def evaluate(x: np.ndarray, y: np.ndarray, labels: list[str], model: dict[str, np.ndarray]) -> dict[str, Any]:
    started = time.perf_counter()
    probs = softmax(x @ model["w"] + model["b"])
    elapsed = time.perf_counter() - started
    pred = probs.argmax(axis=1)
    rows: list[dict[str, Any]] = []
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
        rows.append({"family": label, "precision": float(precision), "recall": float(recall), "f1": float(f1), "support": support})
    benign_id = labels.index("benign") if "benign" in labels else None
    normal_fpr = math.nan
    if benign_id is not None:
        mask = y == benign_id
        if mask.sum() > 0:
            normal_fpr = float((pred[mask] != benign_id).mean())
    metrics: dict[str, Any] = {
        "accuracy": float((pred == y).mean()),
        "macro_f1": float(np.mean(f1s)),
        "normal_fpr": normal_fpr,
        "inference_latency_ms_per_1k": float(elapsed * 1000.0 / max(1.0, len(y) / 1000.0)),
        "per_family": rows,
    }
    metrics.update(calibration_metrics(probs, y, len(labels)))
    return metrics


def write_outputs(out_dir: Path, stem: str, row: dict[str, Any], payload: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{stem}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out_dir / f"{stem}_per_family.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["family", "precision", "recall", "f1", "support"])
        writer.writeheader()
        writer.writerows(payload["metrics"]["per_family"])


def run_one(train_raw: pd.DataFrame, test_raw: pd.DataFrame, args: argparse.Namespace, mode: str, seed: int) -> dict[str, Any]:
    train_df, test_df, cti_meta = cti_feature_frames(train_raw, test_raw, mode, seed)
    spec = fit_feature_spec(train_df, args.max_cat_unique)
    x_train, stats, feature_names = transform_features(train_df, spec, None)
    x_test, _, _ = transform_features(test_df, spec, stats)
    y_train, y_test, labels, label_to_id = encode_labels(train_df, test_df)
    model = train_softmax(x_train, y_train, len(labels), args.epochs, args.batch_size, args.lr, args.weight_decay, seed)
    metrics = evaluate(x_test, y_test, labels, model)
    row = {
        "dataset_name": args.dataset_name,
        "scenario": mode,
        "seed": seed,
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "n_features": int(x_train.shape[1]),
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "normal_fpr": metrics["normal_fpr"],
        "ece": metrics["ece"],
        "brier": metrics["brier"],
        "mean_confidence": metrics["mean_confidence"],
        "inference_latency_ms_per_1k": metrics["inference_latency_ms_per_1k"],
    }
    payload = {
        "dataset_name": args.dataset_name,
        "scenario": mode,
        "seed": seed,
        "train_rows": int(len(y_train)),
        "test_rows": int(len(y_test)),
        "labels": labels,
        "label_to_id": label_to_id,
        "feature_count": int(x_train.shape[1]),
        "feature_names": feature_names,
        "feature_spec": spec,
        "cti_metadata": cti_meta,
        "metrics": metrics,
        "honesty_boundary": "UNSW official train/test baseline. It is a cross-domain dataset result, not Edge-IIoT transfer training.",
    }
    stem = f"{args.dataset_name}_{mode}_seed{seed}"
    write_outputs(Path(args.out_dir), stem, row, payload)
    print(f"scenario={mode} seed={seed} macro_f1={row['macro_f1']:.4f} acc={row['accuracy']:.4f} fpr={row['normal_fpr']:.4f}")
    return row


def write_summary(out_dir: Path, rows: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["dataset_name", "scenario", "seed", "accuracy", "macro_f1", "normal_fpr", "ece", "brier", "mean_confidence", "inference_latency_ms_per_1k", "train_rows", "test_rows", "n_features"]
    with (out_dir / "unsw_nb15_baseline_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in cols})
    (out_dir / "unsw_nb15_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# UNSW-NB15 Bounded Cross-Domain Baseline",
        "",
        "This uses the official UNSW-NB15 train/test parquet files. It is not an Edge-IIoT transfer result.",
        "",
        "## Data",
        "",
        f"- Train rows: {manifest['train_rows']}",
        f"- Test rows: {manifest['test_rows']}",
        f"- Train label counts: `{json.dumps(manifest['train_label_counts'], ensure_ascii=False)}`",
        f"- Test label counts: `{json.dumps(manifest['test_label_counts'], ensure_ascii=False)}`",
        "",
        "## Metrics",
        "",
        "| Scenario | Seed | Macro-F1 | Accuracy | Normal FPR | ECE | Brier |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['seed']} | {row['macro_f1']:.4f} | {row['accuracy']:.4f} | "
            f"{row['normal_fpr']:.4f} | {row['ece']:.4f} | {row['brier']:.4f} |"
        )
    lines.extend([
        "",
        "## Interpretation Guard",
        "",
        "- This result should be compared as a separate cross-domain benchmark, not merged into Edge-IIoT claims.",
        "- Random CTI remains the negative control.",
        "- Any source-gate claim requires a multi-seed mean and comparison with weak CTI and traffic-only.",
    ])
    (out_dir / "unsw_nb15_baseline_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-data", default=None)
    parser.add_argument("--test-data", default=None)
    parser.add_argument("--dataset-name", default="unsw_nb15")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--train-sample-rows", type=int, default=0)
    parser.add_argument("--test-sample-rows", type=int, default=0)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=2048)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--max-cat-unique", type=int, default=80)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument("--modes", nargs="+", default=["traffic_only", "weak_cti_concat", "source_gate", "random_cti"], choices=["traffic_only", "weak_cti_concat", "source_gate", "random_cti"])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_path = find_parquet("UNSW_NB15_training-set.parquet", args.train_data)
    test_path = find_parquet("UNSW_NB15_testing-set.parquet", args.test_data)
    train = read_table(train_path, args.train_sample_rows, args.seeds[0])
    test = read_table(test_path, args.test_sample_rows, args.seeds[0])
    manifest = {
        "train_path": str(train_path),
        "test_path": str(test_path),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_label_counts": {k: int(v) for k, v in train["_family_label"].value_counts().sort_index().items()},
        "test_label_counts": {k: int(v) for k, v in test["_family_label"].value_counts().sort_index().items()},
        "full_dataset_downloaded_locally": False,
        "protocol": "official train/test split with train-fitted preprocessing",
    }
    rows: list[dict[str, Any]] = []
    for seed in args.seeds:
        for mode in args.modes:
            rows.append(run_one(train, test, args, mode, seed))
    write_summary(Path(args.out_dir), rows, manifest)


if __name__ == "__main__":
    main()
