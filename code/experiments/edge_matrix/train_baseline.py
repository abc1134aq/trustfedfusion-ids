#!/usr/bin/env python3
"""Pure NumPy federated IDS baseline for local smoke tests and Kaggle runs."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd


LABEL_CANDIDATES = [
    "Attack_Label",
    "Attack_type",
    "Label",
    "label",
    "class",
    "Attack_label",
    "attack_cat",
]
LABEL_LIKE_COLUMNS = {name.lower() for name in LABEL_CANDIDATES}


def find_label_col(df: pd.DataFrame, requested: str | None) -> str:
    if requested:
        if requested not in df.columns:
            raise ValueError(f"Requested label column not found: {requested}")
        return requested
    for col in LABEL_CANDIDATES:
        if col in df.columns:
            return col
    raise ValueError(f"No label column found. Tried: {LABEL_CANDIDATES}")


def build_features(
    df: pd.DataFrame,
    label_col: str,
    max_cat_unique: int = 20,
) -> tuple[np.ndarray, np.ndarray, list[str], list[str], dict[str, int]]:
    y_raw = df[label_col].astype(str).fillna("UNKNOWN")
    labels = sorted(y_raw.unique().tolist())
    label_to_id = {label: i for i, label in enumerate(labels)}
    y = y_raw.map(label_to_id).to_numpy(dtype=np.int64)

    feature_parts: list[pd.DataFrame] = []
    used_features: list[str] = []
    skipped_features: list[str] = []
    for col in df.columns:
        if col == label_col:
            continue
        if col.lower() in LABEL_LIKE_COLUMNS:
            skipped_features.append(f"{col} (label-like)")
            continue
        series = df[col]
        numeric = pd.to_numeric(series, errors="coerce")
        valid_ratio = float(numeric.notna().mean())
        if valid_ratio >= 0.90:
            median = numeric.median()
            if pd.isna(median):
                median = 0.0
            feature_parts.append(pd.DataFrame({col: numeric.fillna(median).astype(float)}))
            used_features.append(col)
            continue

        nunique = int(series.astype(str).nunique(dropna=True))
        if 1 < nunique <= max_cat_unique:
            encoded = pd.get_dummies(series.astype(str).fillna("MISSING"), prefix=col)
            feature_parts.append(encoded.astype(float))
            used_features.extend(encoded.columns.tolist())
        else:
            skipped_features.append(col)

    if not feature_parts:
        raise ValueError("No usable numeric or low-cardinality categorical features found.")

    x_df = pd.concat(feature_parts, axis=1)
    x = x_df.to_numpy(dtype=np.float64)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    mean = x.mean(axis=0, keepdims=True)
    std = x.std(axis=0, keepdims=True)
    std[std < 1e-8] = 1.0
    x = (x - mean) / std
    return x.astype(np.float32), y, labels, used_features, skipped_features


def stratified_split(y: np.ndarray, test_ratio: float, seed: int) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    train_idx: list[int] = []
    test_idx: list[int] = []
    for label in np.unique(y):
        idx = np.where(y == label)[0]
        rng.shuffle(idx)
        n_test = max(1, int(round(len(idx) * test_ratio)))
        test_idx.extend(idx[:n_test].tolist())
        train_idx.extend(idx[n_test:].tolist())
    rng.shuffle(train_idx)
    rng.shuffle(test_idx)
    return np.array(train_idx, dtype=np.int64), np.array(test_idx, dtype=np.int64)


def make_clients(y: np.ndarray, n_clients: int, partition: str, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    n = len(y)
    if partition == "iid":
        idx = np.arange(n)
        rng.shuffle(idx)
        return [part.astype(np.int64) for part in np.array_split(idx, n_clients)]

    if partition != "label_skew":
        raise ValueError(f"Unknown partition: {partition}")

    sorted_idx = np.argsort(y, kind="stable")
    n_shards = max(n_clients * 2, len(np.unique(y)) * 2)
    shards = [shard for shard in np.array_split(sorted_idx, n_shards) if len(shard) > 0]
    rng.shuffle(shards)
    clients = [[] for _ in range(n_clients)]
    for i, shard in enumerate(shards):
        clients[i % n_clients].extend(shard.tolist())
    return [np.array(c, dtype=np.int64) for c in clients]


def softmax(logits: np.ndarray) -> np.ndarray:
    logits = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(logits)
    return exp / exp.sum(axis=1, keepdims=True)


def predict(x: np.ndarray, weights: dict[str, np.ndarray]) -> np.ndarray:
    logits = x @ weights["w"] + weights["b"]
    return logits.argmax(axis=1)


def predict_proba(x: np.ndarray, weights: dict[str, np.ndarray]) -> np.ndarray:
    return softmax(x @ weights["w"] + weights["b"])


def calibration_metrics(probs: np.ndarray, y: np.ndarray, n_classes: int, n_bins: int = 15) -> dict[str, float]:
    pred = probs.argmax(axis=1)
    confidence = probs.max(axis=1)
    correct = (pred == y).astype(np.float64)
    one_hot = np.eye(n_classes, dtype=np.float64)[y]
    brier = float(np.mean(np.sum((probs.astype(np.float64) - one_hot) ** 2, axis=1)))

    ece = 0.0
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    for lower, upper in zip(bin_edges[:-1], bin_edges[1:]):
        if upper == 1.0:
            mask = (confidence >= lower) & (confidence <= upper)
        else:
            mask = (confidence >= lower) & (confidence < upper)
        if not np.any(mask):
            continue
        bin_acc = float(correct[mask].mean())
        bin_conf = float(confidence[mask].mean())
        ece += float(mask.mean()) * abs(bin_acc - bin_conf)

    return {
        "ece": float(ece),
        "brier": brier,
        "mean_confidence": float(confidence.mean()),
    }


def evaluate(x: np.ndarray, y: np.ndarray, labels: list[str], weights: dict[str, np.ndarray]) -> dict[str, float]:
    probs = predict_proba(x, weights)
    pred = probs.argmax(axis=1)
    accuracy = float((pred == y).mean())
    f1s = []
    for label_id in range(len(labels)):
        tp = float(((pred == label_id) & (y == label_id)).sum())
        fp = float(((pred == label_id) & (y != label_id)).sum())
        fn = float(((pred != label_id) & (y == label_id)).sum())
        precision = tp / (tp + fp + 1e-12)
        recall = tp / (tp + fn + 1e-12)
        f1s.append(2 * precision * recall / (precision + recall + 1e-12))
    normal_ids = [i for i, label in enumerate(labels) if label.lower() in {"normal", "benign"}]
    fpr = math.nan
    if normal_ids:
        normal_mask = np.isin(y, np.array(normal_ids))
        if normal_mask.sum() > 0:
            fpr = float((~np.isin(pred[normal_mask], np.array(normal_ids))).mean())
    return {
        "accuracy": accuracy,
        "macro_f1": float(np.mean(f1s)),
        "fpr_normal": fpr,
        **calibration_metrics(probs, y, len(labels)),
    }


def local_train(
    x: np.ndarray,
    y: np.ndarray,
    idx: np.ndarray,
    global_weights: dict[str, np.ndarray],
    n_classes: int,
    epochs: int,
    batch_size: int,
    lr: float,
    mu: float,
    seed: int,
    label_flip: bool = False,
) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    w = global_weights["w"].copy()
    b = global_weights["b"].copy()
    w0 = global_weights["w"]
    b0 = global_weights["b"]
    for _ in range(epochs):
        shuffled = idx.copy()
        rng.shuffle(shuffled)
        for start in range(0, len(shuffled), batch_size):
            batch = shuffled[start : start + batch_size]
            xb = x[batch]
            yb = y[batch]
            if label_flip:
                yb = (yb + 1) % n_classes
            probs = softmax(xb @ w + b)
            probs[np.arange(len(batch)), yb] -= 1.0
            probs /= max(1, len(batch))
            grad_w = xb.T @ probs + mu * (w - w0)
            grad_b = probs.sum(axis=0) + mu * (b - b0)
            w -= lr * grad_w
            b -= lr * grad_b
    return {"w": w, "b": b}


def flatten_weights(weights: dict[str, np.ndarray]) -> np.ndarray:
    return np.concatenate([weights["w"].ravel(), weights["b"].ravel()])


def unflatten_weights(vector: np.ndarray, template: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    w_size = template["w"].size
    w = vector[:w_size].reshape(template["w"].shape)
    b = vector[w_size:].reshape(template["b"].shape)
    return {"w": w.astype(np.float32), "b": b.astype(np.float32)}


def model_size_mb(weights: dict[str, np.ndarray]) -> float:
    return float(sum(value.nbytes for value in weights.values()) / (1024 * 1024))


def aggregate(
    client_weights: list[dict[str, np.ndarray]],
    client_sizes: list[int],
    aggregator: str,
    trim_ratio: float,
    byzantine_f: int,
) -> dict[str, np.ndarray]:
    if aggregator == "avg":
        return weighted_average(client_weights, client_sizes)

    template = client_weights[0]
    vectors = np.stack([flatten_weights(cw) for cw in client_weights], axis=0)
    if aggregator == "median":
        return unflatten_weights(np.median(vectors, axis=0), template)

    if aggregator == "trimmed_mean":
        m = vectors.shape[0]
        trim = int(math.floor(trim_ratio * m))
        if trim > 0 and 2 * trim < m:
            sorted_vectors = np.sort(vectors, axis=0)
            reduced = sorted_vectors[trim : m - trim]
            return unflatten_weights(reduced.mean(axis=0), template)
        return unflatten_weights(vectors.mean(axis=0), template)

    if aggregator == "krum":
        m = vectors.shape[0]
        f = min(byzantine_f, max(0, (m - 3) // 2))
        keep = max(1, m - f - 2)
        distances = np.sum((vectors[:, None, :] - vectors[None, :, :]) ** 2, axis=2)
        scores = []
        for i in range(m):
            nearest = np.sort(np.delete(distances[i], i))[:keep]
            scores.append(float(nearest.sum()))
        return unflatten_weights(vectors[int(np.argmin(scores))], template)

    raise ValueError(f"Unknown aggregator: {aggregator}")


def weighted_average(client_weights: list[dict[str, np.ndarray]], client_sizes: list[int]) -> dict[str, np.ndarray]:
    total = float(sum(client_sizes))
    w = sum(cw["w"] * (size / total) for cw, size in zip(client_weights, client_sizes))
    b = sum(cw["b"] * (size / total) for cw, size in zip(client_weights, client_sizes))
    return {"w": w, "b": b}


def run_federated(args: argparse.Namespace, x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, y_test: np.ndarray, labels: list[str]) -> list[dict[str, float]]:
    rng = np.random.default_rng(args.seed)
    n_features = x_train.shape[1]
    n_classes = len(labels)
    weights = {
        "w": rng.normal(0.0, 0.01, size=(n_features, n_classes)).astype(np.float32),
        "b": np.zeros(n_classes, dtype=np.float32),
    }
    model_mb = model_size_mb(weights)
    clients = make_clients(y_train, args.clients, args.partition, args.seed)
    n_malicious = int(math.floor(args.clients * args.malicious_ratio))
    malicious_clients = set(range(n_malicious))
    print(f"attack={args.attack} malicious_clients={sorted(malicious_clients)} aggregator={args.aggregator}")
    rows: list[dict[str, float]] = []
    mu = args.mu if args.method == "fedprox" else 0.0
    for rnd in range(1, args.rounds + 1):
        round_started = time.time()
        selected = list(range(args.clients))
        client_weights = []
        client_sizes = []
        for client_id in selected:
            idx = clients[client_id]
            if len(idx) == 0:
                continue
            is_malicious = client_id in malicious_clients and args.attack != "none"
            cw = local_train(
                x_train,
                y_train,
                idx,
                weights,
                n_classes,
                args.local_epochs,
                args.batch_size,
                args.lr,
                mu,
                args.seed + rnd * 1000 + client_id,
                label_flip=(is_malicious and args.attack == "label_flip"),
            )
            if is_malicious and args.attack == "update_scale":
                cw = {
                    "w": weights["w"] + args.attack_scale * (cw["w"] - weights["w"]),
                    "b": weights["b"] + args.attack_scale * (cw["b"] - weights["b"]),
                }
            client_weights.append(cw)
            client_sizes.append(len(idx))
        weights = aggregate(client_weights, client_sizes, args.aggregator, args.trim_ratio, n_malicious)
        metrics = evaluate(x_test, y_test, labels, weights)
        rows.append(
            {
                "round": rnd,
                "method": args.method,
                "partition": args.partition,
                "clients": args.clients,
                "aggregator": args.aggregator,
                "attack": args.attack,
                "malicious_ratio": args.malicious_ratio,
                "train_samples": len(y_train),
                "test_samples": len(y_test),
                **metrics,
            }
        )
        comm_mb_round = model_mb * len(selected) * 2
        round_seconds = time.time() - round_started
        print(
            f"round={rnd:03d} method={args.method} aggregator={args.aggregator} attack={args.attack} partition={args.partition} "
            f"acc={metrics['accuracy']:.4f} macro_f1={metrics['macro_f1']:.4f} fpr={metrics['fpr_normal']} "
            f"ece={metrics['ece']:.4f} brier={metrics['brier']:.4f} conf={metrics['mean_confidence']:.4f} "
            f"comm_mb={comm_mb_round:.4f} round_s={round_seconds:.3f}"
        )
        rows[-1]["model_mb"] = model_mb
        rows[-1]["comm_mb_round"] = comm_mb_round
        rows[-1]["round_seconds"] = round_seconds
    return rows


def run_centralized(args: argparse.Namespace, x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray, y_test: np.ndarray, labels: list[str]) -> list[dict[str, float]]:
    rng = np.random.default_rng(args.seed)
    n_features = x_train.shape[1]
    n_classes = len(labels)
    weights = {
        "w": rng.normal(0.0, 0.01, size=(n_features, n_classes)).astype(np.float32),
        "b": np.zeros(n_classes, dtype=np.float32),
    }
    model_mb = model_size_mb(weights)
    all_idx = np.arange(len(y_train), dtype=np.int64)
    rows = []
    for rnd in range(1, args.rounds + 1):
        round_started = time.time()
        weights = local_train(
            x_train,
            y_train,
            all_idx,
            weights,
            n_classes,
            args.local_epochs,
            args.batch_size,
            args.lr,
            0.0,
            args.seed + rnd,
        )
        metrics = evaluate(x_test, y_test, labels, weights)
        rows.append(
            {
                "round": rnd,
                "method": "centralized",
                "partition": "centralized",
                "clients": 1,
                "train_samples": len(y_train),
                "test_samples": len(y_test),
                "model_mb": model_mb,
                "comm_mb_round": 0.0,
                "round_seconds": time.time() - round_started,
                **metrics,
            }
        )
        print(
            f"round={rnd:03d} method=centralized acc={metrics['accuracy']:.4f} macro_f1={metrics['macro_f1']:.4f} "
            f"ece={metrics['ece']:.4f} brier={metrics['brier']:.4f} conf={metrics['mean_confidence']:.4f}"
        )
    return rows


def write_outputs(args: argparse.Namespace, rows: list[dict[str, float]], meta: dict[str, object]) -> None:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    attack_suffix = args.attack
    if args.attack != "none":
        ratio_slug = str(args.malicious_ratio).replace(".", "p")
        attack_suffix = f"{args.attack}_mal{ratio_slug}"
    stem = f"{args.dataset_name}_{args.method}_{args.aggregator}_{attack_suffix}_{args.partition}_seed{args.seed}"
    csv_path = out_dir / f"{stem}.csv"
    json_path = out_dir / f"{stem}.json"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps({**meta, "results": rows}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {csv_path}")
    print(f"wrote {json_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=None)
    parser.add_argument("--dataset-name", default="dataset")
    parser.add_argument("--label-col", default=None)
    parser.add_argument("--method", choices=["centralized", "fedavg", "fedprox"], default="fedavg")
    parser.add_argument("--aggregator", choices=["avg", "median", "trimmed_mean", "krum"], default="avg")
    parser.add_argument("--trim-ratio", type=float, default=0.2)
    parser.add_argument("--attack", choices=["none", "label_flip", "update_scale"], default="none")
    parser.add_argument("--malicious-ratio", type=float, default=0.0)
    parser.add_argument("--attack-scale", type=float, default=5.0)
    parser.add_argument("--partition", choices=["iid", "label_skew"], default="label_skew")
    parser.add_argument("--clients", type=int, default=10)
    parser.add_argument("--rounds", type=int, default=30)
    parser.add_argument("--local-epochs", type=int, default=1)
    parser.add_argument("--batch-size", type=int, default=256)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--mu", type=float, default=0.01)
    parser.add_argument("--test-ratio", type=float, default=0.2)
    parser.add_argument("--sample-size", type=int, default=0)
    parser.add_argument("--max-cat-unique", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default="04_Results/metrics")
    args = parser.parse_args()

    started = time.time()
    if args.data is None:
        candidates = [
            ("/kaggle/input/edge-iiot-ml-clean-trustfedfusion/edge_iiot_ml_clean_full.csv", "edge_iiot_ml_clean_full"),
            ("/kaggle/input/edge-iiot-ml-clean-trustfedfusion/edge_iiot_ml_clean_50001.csv", "edge_iiot_ml_clean_sample"),
            ("02_Data/processed/edge_iiot_ml_clean_full.csv", "edge_iiot_ml_clean_full"),
            ("02_Data/processed/edge_iiot_ml_clean_50001.csv", "edge_iiot_ml_clean_sample"),
            ("/kaggle/input/edge-iiot-balanced-subset-for-intrusion-detection/edge_iiot.csv", "edge_iiot_balanced"),
            ("/kaggle/input/edge-iiotset-dataset/ML-EdgeIIoT-dataset.csv", "edge_iiot_ml"),
            ("02_Data/kaggle/edge_iiot_ml/ML-EdgeIIoT-dataset.csv", "edge_iiot_ml"),
            ("02_Data/kaggle/edge_iiot_balanced/edge_iiot.csv", "edge_iiot_balanced"),
        ]
        for candidate, name in candidates:
            if Path(candidate).exists():
                args.data = candidate
                if args.dataset_name == "dataset":
                    args.dataset_name = name
                break
        if args.data is None and Path("/kaggle/input").exists():
            recursive_candidates = [
                ("edge_iiot_ml_clean_full.csv", "edge_iiot_ml_clean_full"),
                ("edge_iiot_ml_clean_50001.csv", "edge_iiot_ml_clean_sample"),
                ("edge_iiot.csv", "edge_iiot_balanced"),
                ("ML-EdgeIIoT-dataset.csv", "edge_iiot_ml"),
                ("Merged01.csv", "ciciot2023_small"),
                ("train.csv", "ciciot2023_train"),
            ]
            for filename, name in recursive_candidates:
                matches = sorted(Path("/kaggle/input").rglob(filename))
                if matches:
                    args.data = str(matches[0])
                    if args.dataset_name == "dataset":
                        args.dataset_name = name
                    break
        if args.data is None:
            available = []
            if Path("/kaggle/input").exists():
                available = [str(p) for p in Path("/kaggle/input").rglob("*") if p.is_file()][:50]
            raise ValueError(f"No --data supplied and no known Kaggle/local dataset file found. Available files: {available}")

    data_path = Path(args.data)
    read_nrows = args.sample_size if args.sample_size and args.sample_size > 0 else None
    df = pd.read_csv(data_path, low_memory=False, nrows=read_nrows)
    if args.sample_size and args.sample_size < len(df):
        df = df.sample(n=args.sample_size, random_state=args.seed).reset_index(drop=True)
    label_col = find_label_col(df, args.label_col)
    x, y, labels, used_features, skipped_features = build_features(df, label_col, args.max_cat_unique)
    train_idx, test_idx = stratified_split(y, args.test_ratio, args.seed)
    x_train, y_train = x[train_idx], y[train_idx]
    x_test, y_test = x[test_idx], y[test_idx]

    print(f"dataset={args.dataset_name} rows={len(df)} features={x.shape[1]} classes={len(labels)} label_col={label_col}")
    print(f"labels={labels}")
    print(f"used_features={len(used_features)} skipped_features={len(skipped_features)}")

    if args.method == "centralized":
        rows = run_centralized(args, x_train, y_train, x_test, y_test, labels)
    else:
        rows = run_federated(args, x_train, y_train, x_test, y_test, labels)

    meta = {
        "data": str(data_path),
        "dataset_name": args.dataset_name,
        "label_col": label_col,
        "labels": labels,
        "used_features": used_features,
        "skipped_features": skipped_features,
        "elapsed_seconds": round(time.time() - started, 3),
        "args": vars(args),
    }
    write_outputs(args, rows, meta)


def find_clean_file_for_matrix() -> str:
    candidates = [
        "/kaggle/input/edge-iiot-ml-clean-trustfedfusion/edge_iiot_ml_clean_full.csv",
        "/kaggle/input/edge-iiot-ml-clean-trustfedfusion/edge_iiot_ml_clean_50001.csv",
        "02_Data/processed/edge_iiot_ml_clean_full.csv",
        "02_Data/processed/edge_iiot_ml_clean_50001.csv",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    if Path("/kaggle/input").exists():
        for pattern in ["edge_iiot_ml_clean_full.csv", "edge_iiot_ml_clean_*.csv"]:
            matches = sorted(Path("/kaggle/input").rglob(pattern))
            if matches:
                return str(matches[0])
    raise FileNotFoundError("Clean Edge-IIoT ML CSV not found.")


def run_matrix_one(data_path: str, cfg: dict[str, object]) -> None:
    args = [
        "train_baseline.py",
        "--data",
        data_path,
        "--dataset-name",
        "edge_iiot_ml_clean_full",
        "--label-col",
        "Attack_type",
        "--method",
        str(cfg["method"]),
        "--aggregator",
        str(cfg["aggregator"]),
        "--attack",
        str(cfg["attack"]),
        "--partition",
        "label_skew",
        "--clients",
        "10",
        "--rounds",
        str(cfg["rounds"]),
        "--local-epochs",
        "1",
        "--sample-size",
        "0",
        "--seed",
        "42",
        "--out-dir",
        "04_Results/metrics",
    ]
    if cfg["attack"] != "none":
        args.extend(["--malicious-ratio", str(cfg["malicious_ratio"])])
    if cfg["method"] == "fedprox":
        args.extend(["--mu", "0.01"])
    print("\n=== RUN", json.dumps(cfg, ensure_ascii=False), "===")
    sys.argv = args
    main()


def main_matrix() -> None:
    data_path = find_clean_file_for_matrix()
    scenarios: list[dict[str, object]] = [
        {"name": "clean_fedavg_50", "method": "fedavg", "aggregator": "avg", "attack": "none", "malicious_ratio": 0.0, "rounds": 50},
        {"name": "clean_fedprox_50", "method": "fedprox", "aggregator": "avg", "attack": "none", "malicious_ratio": 0.0, "rounds": 50},
    ]
    for attack in ["label_flip", "update_scale"]:
        for aggregator in ["avg", "median", "trimmed_mean", "krum"]:
            scenarios.append(
                {
                    "name": f"{attack}_{aggregator}_mal0p2_30",
                    "method": "fedavg",
                    "aggregator": aggregator,
                    "attack": attack,
                    "malicious_ratio": 0.2,
                    "rounds": 30,
                }
            )

    manifest = {
        "purpose": "Kaggle CPU matrix: clean 50-round baselines and 20% malicious poisoning calibration rerun.",
        "data_path": data_path,
        "scenarios": scenarios,
    }
    Path("04_Results/metrics").mkdir(parents=True, exist_ok=True)
    Path("04_Results/metrics/kaggle_matrix_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    for cfg in scenarios:
        run_matrix_one(data_path, cfg)


if __name__ == "__main__":
    main_matrix()
