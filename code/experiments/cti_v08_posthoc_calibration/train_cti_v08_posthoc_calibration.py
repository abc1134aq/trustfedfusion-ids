#!/usr/bin/env python3
"""TrustFedFusion v0.8: post-hoc source-aware calibration.

v0.7 showed that selecting source-gate alpha with an ECE/Brier objective
preserved the F1/FPR gain but did not reduce ECE. v0.8 keeps the classifier
and alpha-selection protocol intact, then tests post-hoc source-aware
temperature calibration on validation-only gate-intensity bins.
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
DEFAULT_OUT_DIR = Path("04_Results/cti_v08_posthoc_calibration")
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
    candidates = [Path(f"02_Data/kaggle/unsw_nb15/{name}"), INPUT_ROOT / "unswnb15" / name]
    if INPUT_ROOT.exists():
        candidates.extend(sorted(INPUT_ROOT.rglob(name)))
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"Could not find {name}; pass explicit --train-data/--test-data.")


def read_table(path: Path) -> pd.DataFrame:
    df = pd.read_parquet(path) if path.suffix.lower() == ".parquet" else pd.read_csv(path, low_memory=False)
    df.columns = df.columns.astype(str)
    if LABEL_COL not in df.columns:
        raise ValueError(f"Expected label column {LABEL_COL}, got {df.columns.tolist()}")
    out = df.copy()
    out["_family_label"] = out[LABEL_COL].map(normalize_label)
    return out


def stratified_valid_split(df: pd.DataFrame, valid_ratio: float, seed: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    rng = np.random.default_rng(seed)
    train_idx: list[int] = []
    valid_idx: list[int] = []
    for _, group in df.groupby("_family_label", sort=True):
        idx = group.index.to_numpy()
        rng.shuffle(idx)
        n_valid = max(1, int(round(len(idx) * valid_ratio))) if len(idx) > 2 else 0
        valid_idx.extend(idx[:n_valid].tolist())
        train_idx.extend(idx[n_valid:].tolist())
    rng.shuffle(train_idx)
    rng.shuffle(valid_idx)
    return df.loc[train_idx].reset_index(drop=True), df.loc[valid_idx].reset_index(drop=True)


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


def make_cti_specs(reference_train: pd.DataFrame, frame: pd.DataFrame) -> list[tuple[str, pd.Series, str]]:
    return [
        ("_cti_proto_tcp", (frame["proto"].astype(str).str.lower() == "tcp").astype(float), "tcp"),
        ("_cti_proto_udp", (frame["proto"].astype(str).str.lower() == "udp").astype(float), "udp"),
        ("_cti_service_http", frame["service"].astype(str).str.lower().isin({"http", "ssl", "ftp", "ftp-data"}).astype(float), "service"),
        ("_cti_service_dns", frame["service"].astype(str).str.lower().isin({"dns"}).astype(float), "service"),
        ("_cti_state_int", (frame["state"].astype(str).str.upper() == "INT").astype(float), "tcp_state"),
        ("_cti_state_fin", (frame["state"].astype(str).str.upper() == "FIN").astype(float), "tcp_state"),
        ("_cti_rate_high", high_from_train(numeric_series(reference_train, "rate"), numeric_series(frame, "rate")), "rate"),
        ("_cti_sload_high", high_from_train(numeric_series(reference_train, "sload"), numeric_series(frame, "sload")), "rate"),
        ("_cti_dload_high", high_from_train(numeric_series(reference_train, "dload"), numeric_series(frame, "dload")), "rate"),
        ("_cti_sbytes_high", high_from_train(numeric_series(reference_train, "sbytes"), numeric_series(frame, "sbytes")), "flow"),
        ("_cti_dbytes_high", high_from_train(numeric_series(reference_train, "dbytes"), numeric_series(frame, "dbytes")), "flow"),
        ("_cti_tcprtt_high", high_from_train(numeric_series(reference_train, "tcprtt"), numeric_series(frame, "tcprtt")), "tcp"),
    ]


def add_cti_to_frames(
    train: pd.DataFrame,
    valid: pd.DataFrame,
    test: pd.DataFrame,
    mode: str,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    if mode == "traffic_only":
        return train.copy(), valid.copy(), test.copy(), {"cti_mode": mode, "cti_columns": []}

    source_gate_modes = {"source_gate", "source_gate_pruned", "cal_source_gate", "cal_source_gate_ece", "random_source_gate", "cal_random_source_gate", "cal_random_source_gate_ece"}
    randomized_modes = {"random_cti", "random_source_gate", "cal_random_source_gate", "cal_random_source_gate_ece"}
    effective_mode = "source_gate" if mode in source_gate_modes else mode
    rng = np.random.default_rng(seed)
    outputs = [train.copy(), valid.copy(), test.copy()]
    cti_cols: list[str] = []
    sources: dict[str, str] = {}
    for frame_idx, frame in enumerate(outputs):
        specs = make_cti_specs(train, frame)
        for col, values, source in specs:
            arr = values.to_numpy(dtype=float)
            if mode in randomized_modes:
                rng.shuffle(arr)
            frame[col] = arr.astype(float)
            if frame_idx == 0:
                cti_cols.append(col)
                sources[col] = source

    if effective_mode == "source_gate":
        for frame in outputs:
            gate_cols: list[str] = []
            for source, reliability in CTI_SOURCE_RELIABILITY.items():
                cols = [col for col in cti_cols if sources[col] == source]
                if not cols:
                    continue
                active = np.zeros(len(frame), dtype=float)
                for col in cols:
                    active += (frame[col].to_numpy(dtype=float) > 0).astype(float)
                saturation = max(1.0, min(3.0, float(len(cols))))
                gate = reliability * np.minimum(active / saturation, 1.0)
                active_col = f"_cti_{source}_active_count"
                gate_col = f"_cti_{source}_gate"
                frame[active_col] = active.astype(float)
                frame[gate_col] = gate.astype(float)
                gate_cols.extend([active_col, gate_col])
                for col in cols:
                    gated_col = f"{col}_source_gate"
                    frame[gated_col] = frame[col].to_numpy(dtype=float) * gate
                    gate_cols.append(gated_col)
            summary_cols = [col for col in frame.columns if col.endswith("_gate") and col.startswith("_cti_")]
            if summary_cols:
                gate_stack = np.stack([frame[col].to_numpy(dtype=float) for col in summary_cols], axis=1)
                frame["_cti_source_gate_mean"] = gate_stack.mean(axis=1)
                frame["_cti_source_gate_max"] = gate_stack.max(axis=1)
                gate_cols.extend(["_cti_source_gate_mean", "_cti_source_gate_max"])
            if mode == "source_gate_pruned":
                keep = set(gate_cols)
                drop_cols = [col for col in frame.columns if col.startswith("_cti_") and col not in keep]
                frame.drop(columns=drop_cols, inplace=True)

    final_cti_cols = [col for col in outputs[0].columns if col.startswith("_cti_")]
    return outputs[0], outputs[1], outputs[2], {
        "cti_mode": mode,
        "effective_mode": effective_mode,
        "cti_columns": final_cti_cols,
        "source_reliability": CTI_SOURCE_RELIABILITY,
        "leakage_guard": "Weak CTI hints use only UNSW flow/protocol/service/state fields, never attack_cat or label.",
        "randomized_cti": mode in randomized_modes,
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


def transform(df: pd.DataFrame, spec: dict[str, Any], stats: dict[str, Any] | None = None) -> tuple[np.ndarray, dict[str, Any], list[str]]:
    parts: list[np.ndarray] = []
    names: list[str] = []
    out_stats = {} if stats is None else stats
    for col in spec["numeric_cols"]:
        values = pd.to_numeric(df[col], errors="coerce").replace([np.inf, -np.inf], np.nan)
        if stats is None:
            median = float(values.median()) if not pd.isna(values.median()) else 0.0
            filled = values.fillna(median).to_numpy(dtype=np.float64)
            mean = float(filled.mean())
            std = float(filled.std())
            if std < 1e-8:
                std = 1.0
            out_stats[col] = {"median": median, "mean": mean, "std": std}
        st = out_stats[col]
        arr = values.fillna(st["median"]).to_numpy(dtype=np.float64)
        parts.append(((arr - st["mean"]) / st["std"]).reshape(-1, 1))
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
    return x, out_stats, names


def apply_cti_alpha(x: np.ndarray, feature_names: list[str], alpha: float) -> np.ndarray:
    """Scale CTI-derived columns after standardization so alpha is not cancelled."""
    out = x.copy()
    cti_idx = [i for i, name in enumerate(feature_names) if name.startswith("_cti_")]
    if cti_idx:
        out[:, cti_idx] *= float(alpha)
    return out


def stratified_cap(df: pd.DataFrame, max_rows: int | None, seed: int) -> pd.DataFrame:
    if not max_rows or max_rows <= 0 or len(df) <= max_rows:
        return df.reset_index(drop=True)
    rng = np.random.default_rng(seed)
    pieces: list[pd.DataFrame] = []
    counts = df["_family_label"].value_counts()
    for label, count in counts.items():
        quota = max(1, int(round(max_rows * count / len(df))))
        group = df[df["_family_label"] == label]
        take = min(len(group), quota)
        idx = rng.choice(group.index.to_numpy(), size=take, replace=False)
        pieces.append(df.loc[idx])
    out = pd.concat(pieces, axis=0)
    if len(out) > max_rows:
        out = out.sample(n=max_rows, random_state=seed)
    return out.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def encode(train: pd.DataFrame, valid: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], dict[str, int]]:
    labels = sorted(train["_family_label"].astype(str).unique().tolist())
    label_to_id = {label: i for i, label in enumerate(labels)}
    y_train = train["_family_label"].astype(str).map(label_to_id).to_numpy(dtype=np.int64)
    y_valid = valid["_family_label"].astype(str).map(label_to_id).fillna(-1).to_numpy(dtype=np.int64)
    y_test = test["_family_label"].astype(str).map(label_to_id).fillna(-1).to_numpy(dtype=np.int64)
    if (y_valid < 0).any() or (y_test < 0).any():
        raise ValueError("Validation/test label not present in train labels.")
    return y_train, y_valid, y_test, labels, label_to_id


def softmax_logits(logits: np.ndarray, temperature: float = 1.0) -> np.ndarray:
    logits = logits / max(temperature, 1e-6)
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
    label_smoothing: float = 0.0,
    confidence_penalty: float = 0.0,
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
            probs = softmax_logits(xb @ w + b)
            row_weights = class_weights[yb].astype(np.float32)
            if label_smoothing > 0:
                smooth = min(max(float(label_smoothing), 0.0), 0.5)
                target = np.full_like(probs, smooth / float(n_classes), dtype=np.float32)
                target[np.arange(len(batch)), yb] += 1.0 - smooth
                grad_logits = probs - target
            else:
                grad_logits = probs.copy()
                grad_logits[np.arange(len(batch)), yb] -= 1.0
            if confidence_penalty > 0:
                # Gradient of sum_k p_k log(p_k); positive weight encourages less overconfident predictions.
                logp = np.log(np.clip(probs, 1e-12, 1.0))
                expected_logp = (probs * logp).sum(axis=1, keepdims=True)
                grad_logits += float(confidence_penalty) * probs * (logp - expected_logp)
            grad_logits *= row_weights[:, None]
            grad_logits /= max(1, len(batch))
            grad_w = xb.T @ grad_logits + weight_decay * w
            grad_b = grad_logits.sum(axis=0)
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


def nll(logits: np.ndarray, y: np.ndarray, temperature: float) -> float:
    probs = softmax_logits(logits, temperature)
    return float(-np.log(probs[np.arange(len(y)), y] + 1e-12).mean())


def fit_temperature(logits: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    candidates = np.concatenate([np.linspace(0.5, 3.0, 26), np.linspace(3.25, 8.0, 20)])
    pairs = [(float(t), nll(logits, y, float(t))) for t in candidates]
    return min(pairs, key=lambda item: item[1])


def gate_scores_from_frame(frame: pd.DataFrame) -> np.ndarray:
    """Return source-gate intensity without using labels."""
    if "_cti_source_gate_mean" in frame.columns:
        return pd.to_numeric(frame["_cti_source_gate_mean"], errors="coerce").fillna(0.0).to_numpy(dtype=float)
    gate_cols = [col for col in frame.columns if col.startswith("_cti_") and col.endswith("_gate")]
    if not gate_cols:
        return np.zeros(len(frame), dtype=float)
    values = [pd.to_numeric(frame[col], errors="coerce").fillna(0.0).to_numpy(dtype=float) for col in gate_cols]
    return np.stack(values, axis=1).mean(axis=1)


def fit_gate_binned_temperature(
    logits: np.ndarray,
    y: np.ndarray,
    gate_scores: np.ndarray,
    n_bins: int,
    min_group_size: int = 50,
) -> dict[str, Any]:
    """Fit scalar temperatures separately for validation-only gate-intensity bins."""
    global_temp, global_nll = fit_temperature(logits, y)
    gate_scores = np.asarray(gate_scores, dtype=float)
    if n_bins <= 1 or len(np.unique(gate_scores)) <= 1:
        return {"n_bins": 1, "thresholds": [], "temperatures": [global_temp], "group_sizes": [int(len(y))], "global_temperature": global_temp, "global_nll": global_nll}
    quantiles = np.linspace(0.0, 1.0, n_bins + 1)[1:-1]
    thresholds = np.unique(np.quantile(gate_scores, quantiles)).astype(float)
    if len(thresholds) == 0:
        return {"n_bins": 1, "thresholds": [], "temperatures": [global_temp], "group_sizes": [int(len(y))], "global_temperature": global_temp, "global_nll": global_nll}
    groups = np.digitize(gate_scores, thresholds, right=True)
    temperatures: list[float] = []
    group_sizes: list[int] = []
    for group_id in range(len(thresholds) + 1):
        mask = groups == group_id
        group_sizes.append(int(mask.sum()))
        if int(mask.sum()) < min_group_size or len(np.unique(y[mask])) < 2:
            temperatures.append(float(global_temp))
            continue
        temp, _ = fit_temperature(logits[mask], y[mask])
        temperatures.append(float(temp))
    return {
        "n_bins": int(len(thresholds) + 1),
        "thresholds": [float(x) for x in thresholds],
        "temperatures": temperatures,
        "group_sizes": group_sizes,
        "global_temperature": float(global_temp),
        "global_nll": float(global_nll),
    }


def softmax_gate_binned_temperature(logits: np.ndarray, gate_scores: np.ndarray, spec: dict[str, Any]) -> np.ndarray:
    thresholds = np.asarray(spec.get("thresholds", []), dtype=float)
    temperatures = np.asarray(spec.get("temperatures", [spec.get("global_temperature", 1.0)]), dtype=float)
    groups = np.digitize(np.asarray(gate_scores, dtype=float), thresholds, right=True)
    probs = np.zeros_like(logits, dtype=float)
    for group_id in range(len(temperatures)):
        mask = groups == group_id
        if np.any(mask):
            probs[mask] = softmax_logits(logits[mask], float(temperatures[group_id]))
    return probs


def evaluate(logits: np.ndarray, y: np.ndarray, labels: list[str], temperature: float) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    raw_probs = softmax_logits(logits, 1.0)
    temp_probs = softmax_logits(logits, temperature)
    pred = raw_probs.argmax(axis=1)
    rows: list[dict[str, Any]] = []
    f1s: list[float] = []
    for i, label in enumerate(labels):
        tp = float(((pred == i) & (y == i)).sum())
        fp = float(((pred == i) & (y != i)).sum())
        fn = float(((pred != i) & (y == i)).sum())
        precision = tp / (tp + fp + 1e-12)
        recall = tp / (tp + fn + 1e-12)
        f1 = 2 * precision * recall / (precision + recall + 1e-12)
        f1s.append(f1)
        rows.append({"family": label, "precision": precision, "recall": recall, "f1": f1, "support": int((y == i).sum())})
    benign_id = labels.index("benign") if "benign" in labels else None
    normal_fpr = math.nan
    if benign_id is not None:
        mask = y == benign_id
        if mask.sum() > 0:
            normal_fpr = float((pred[mask] != benign_id).mean())
    raw_cal = calibration_metrics(raw_probs, y, len(labels))
    temp_cal = calibration_metrics(temp_probs, y, len(labels))
    metrics: dict[str, Any] = {
        "accuracy": float((pred == y).mean()),
        "macro_f1": float(np.mean(f1s)),
        "normal_fpr": normal_fpr,
        "temperature": float(temperature),
        "raw_ece": raw_cal["ece"],
        "raw_brier": raw_cal["brier"],
        "raw_mean_confidence": raw_cal["mean_confidence"],
        "temp_ece": temp_cal["ece"],
        "temp_brier": temp_cal["brier"],
        "temp_mean_confidence": temp_cal["mean_confidence"],
    }
    return metrics, rows


def run_one(train_all: pd.DataFrame, test_raw: pd.DataFrame, args: argparse.Namespace, mode: str, seed: int) -> dict[str, Any]:
    train_core, valid_raw = stratified_valid_split(train_all, args.valid_ratio, seed)
    train_core = stratified_cap(train_core, args.max_train_rows, seed)
    valid_raw = stratified_cap(valid_raw, args.max_valid_rows, seed + 10_000)
    test_raw = stratified_cap(test_raw, args.max_test_rows, seed + 20_000)
    train_df, valid_df, test_df, cti_meta = add_cti_to_frames(train_core, valid_raw, test_raw, mode, seed)
    spec = fit_feature_spec(train_df, args.max_cat_unique)
    x_train, stats, feature_names = transform(train_df, spec, None)
    x_valid, _, _ = transform(valid_df, spec, stats)
    x_test, _, _ = transform(test_df, spec, stats)
    y_train, y_valid, y_test, labels, label_to_id = encode(train_df, valid_df, test_df)

    cal_modes = {"cal_source_gate", "cal_source_gate_ece", "cal_random_source_gate", "cal_random_source_gate_ece"}
    candidates: list[dict[str, Any]] = []
    selected_alpha = 1.0
    selected_model: dict[str, np.ndarray] | None = None
    selected_valid_logits: np.ndarray | None = None
    selected_x_test = x_test
    if mode in cal_modes:
        best_f1 = -1.0
        best_score = -1e18
        for alpha in args.alpha_grid:
            x_train_alpha = apply_cti_alpha(x_train, feature_names, alpha)
            x_valid_alpha = apply_cti_alpha(x_valid, feature_names, alpha)
            model = train_softmax(
                x_train_alpha,
                y_train,
                len(labels),
                args.epochs,
                args.batch_size,
                args.lr,
                args.weight_decay,
                seed,
                label_smoothing=args.label_smoothing,
                confidence_penalty=args.confidence_penalty,
            )
            valid_logits = x_valid_alpha @ model["w"] + model["b"]
            temperature, valid_nll = fit_temperature(valid_logits, y_valid)
            valid_metrics, _ = evaluate(valid_logits, y_valid, labels, temperature=1.0)
            composite_score = (
                float(valid_metrics["macro_f1"])
                - float(args.ece_penalty) * float(valid_metrics["raw_ece"])
                - float(args.brier_penalty) * float(valid_metrics["raw_brier"])
            )
            candidate = {
                "alpha": float(alpha),
                "valid_macro_f1": valid_metrics["macro_f1"],
                "valid_accuracy": valid_metrics["accuracy"],
                "valid_raw_ece": valid_metrics["raw_ece"],
                "valid_raw_brier": valid_metrics["raw_brier"],
                "valid_composite_score": composite_score,
                "valid_nll": valid_nll,
                "temperature": temperature,
                "model": model,
                "valid_logits": valid_logits,
            }
            candidates.append(candidate)
            best_f1 = max(best_f1, float(valid_metrics["macro_f1"]))
            best_score = max(best_score, composite_score)
        if mode.endswith("_ece"):
            selected = max(
                candidates,
                key=lambda c: (
                    float(c["valid_composite_score"]),
                    -float(c["valid_raw_ece"]),
                    float(c["valid_macro_f1"]),
                    -float(c["alpha"]),
                ),
            )
            tolerance = None
            selection_rule = "maximize validation Macro-F1 minus ECE/Brier penalties"
        else:
            tolerance = max(float(args.alpha_f1_abs_tolerance), abs(best_f1) * float(args.alpha_f1_rel_tolerance))
            eligible = [c for c in candidates if float(c["valid_macro_f1"]) >= best_f1 - tolerance]
            selected = min(
                eligible,
                key=lambda c: (
                    float(c["valid_raw_ece"]),
                    float(c["valid_nll"]),
                    -float(c["valid_macro_f1"]),
                    float(c["alpha"]),
                ),
            )
            selection_rule = "select the lowest validation raw ECE among candidates within the validation Macro-F1 tolerance band"
        selected_alpha = float(selected["alpha"])
        selected_model = selected["model"]
        selected_valid_logits = selected["valid_logits"]
        selected_x_test = apply_cti_alpha(x_test, feature_names, selected_alpha)
        cti_meta["alpha_selection"] = {
            "rule": selection_rule,
            "alpha_grid": [float(x) for x in args.alpha_grid],
            "selected_alpha": selected_alpha,
            "best_valid_macro_f1": best_f1,
            "best_valid_composite_score": best_score,
            "f1_tolerance": tolerance,
            "ece_penalty": args.ece_penalty,
            "brier_penalty": args.brier_penalty,
            "label_smoothing": args.label_smoothing,
            "confidence_penalty": args.confidence_penalty,
            "post_standardization_scaling": True,
        }
    else:
        selected_model = train_softmax(
            x_train,
            y_train,
            len(labels),
            args.epochs,
            args.batch_size,
            args.lr,
            args.weight_decay,
            seed,
            label_smoothing=0.0,
            confidence_penalty=0.0,
        )
        selected_valid_logits = x_valid @ selected_model["w"] + selected_model["b"]

    assert selected_model is not None
    assert selected_valid_logits is not None
    temperature, valid_nll = fit_temperature(selected_valid_logits, y_valid)
    valid_metrics, _ = evaluate(selected_valid_logits, y_valid, labels, temperature=1.0)
    started = time.perf_counter()
    test_logits = selected_x_test @ selected_model["w"] + selected_model["b"]
    inference_seconds = time.perf_counter() - started
    metrics, per_family = evaluate(test_logits, y_test, labels, temperature)
    valid_gate_scores = gate_scores_from_frame(valid_df)
    test_gate_scores = gate_scores_from_frame(test_df)
    group2_spec = fit_gate_binned_temperature(selected_valid_logits, y_valid, valid_gate_scores, n_bins=2, min_group_size=args.min_group_size)
    group3_spec = fit_gate_binned_temperature(selected_valid_logits, y_valid, valid_gate_scores, n_bins=3, min_group_size=args.min_group_size)
    group2_probs = softmax_gate_binned_temperature(test_logits, test_gate_scores, group2_spec)
    group3_probs = softmax_gate_binned_temperature(test_logits, test_gate_scores, group3_spec)
    group2_cal = calibration_metrics(group2_probs, y_test, len(labels))
    group3_cal = calibration_metrics(group3_probs, y_test, len(labels))
    row = {
        "dataset_name": args.dataset_name,
        "scenario": mode,
        "seed": seed,
        "train_rows": int(len(y_train)),
        "valid_rows": int(len(y_valid)),
        "test_rows": int(len(y_test)),
        "n_features": int(x_train.shape[1]),
        "selected_alpha": selected_alpha,
        "label_smoothing": float(args.label_smoothing if mode in cal_modes else 0.0),
        "confidence_penalty": float(args.confidence_penalty if mode in cal_modes else 0.0),
        "valid_macro_f1": valid_metrics["macro_f1"],
        "valid_raw_ece": valid_metrics["raw_ece"],
        "accuracy": metrics["accuracy"],
        "macro_f1": metrics["macro_f1"],
        "normal_fpr": metrics["normal_fpr"],
        "temperature": metrics["temperature"],
        "valid_nll": valid_nll,
        "raw_ece": metrics["raw_ece"],
        "raw_brier": metrics["raw_brier"],
        "raw_mean_confidence": metrics["raw_mean_confidence"],
        "temp_ece": metrics["temp_ece"],
        "temp_brier": metrics["temp_brier"],
        "temp_mean_confidence": metrics["temp_mean_confidence"],
        "group2_temp_ece": group2_cal["ece"],
        "group2_temp_brier": group2_cal["brier"],
        "group2_temp_mean_confidence": group2_cal["mean_confidence"],
        "group3_temp_ece": group3_cal["ece"],
        "group3_temp_brier": group3_cal["brier"],
        "group3_temp_mean_confidence": group3_cal["mean_confidence"],
        "group2_temperatures": json.dumps(group2_spec["temperatures"]),
        "group3_temperatures": json.dumps(group3_spec["temperatures"]),
        "inference_latency_ms_per_1k": float(inference_seconds * 1000.0 / max(1.0, len(y_test) / 1000.0)),
    }
    payload = {
        "dataset_name": args.dataset_name,
        "scenario": mode,
        "seed": seed,
        "labels": labels,
        "label_to_id": label_to_id,
        "feature_count": int(x_train.shape[1]),
        "feature_names": feature_names,
        "feature_spec": spec,
        "cti_metadata": cti_meta,
        "metrics": metrics,
        "posthoc_calibration": {
            "gate_scores": "validation/test source-gate intensity; labels are not used to form bins",
            "group2": {"spec": group2_spec, "test": group2_cal},
            "group3": {"spec": group3_spec, "test": group3_cal},
            "macro_f1_invariance": "Gate-binned temperature scaling changes probabilities only; raw-logit predictions and Macro-F1 are unchanged.",
        },
        "per_family": per_family,
        "alpha_candidates": [
            {k: v for k, v in candidate.items() if k not in {"model", "valid_logits"}}
            for candidate in candidates
        ],
        "honesty_boundary": "v0.8 uses validation-only post-hoc gate-binned temperature scaling. It cannot be claimed as a new classifier improvement unless calibration improves without hiding F1/FPR trade-offs.",
    }
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.dataset_name}_{mode}_seed{seed}"
    (out_dir / f"{stem}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    with (out_dir / f"{stem}_per_family.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["family", "precision", "recall", "f1", "support"])
        writer.writeheader()
        writer.writerows(per_family)
    print(
        f"scenario={mode} seed={seed} macro_f1={row['macro_f1']:.4f} "
        f"raw_ece={row['raw_ece']:.4f} temp_ece={row['temp_ece']:.4f} "
        f"group2_ece={row['group2_temp_ece']:.4f} group3_ece={row['group3_temp_ece']:.4f} "
        f"alpha={row['selected_alpha']:.2f} temp={row['temperature']:.2f}"
    )
    return row


def write_summary(rows: list[dict[str, Any]], manifest: dict[str, Any], out_dir: Path) -> None:
    cols = [
        "dataset_name",
        "scenario",
        "seed",
        "selected_alpha",
        "label_smoothing",
        "confidence_penalty",
        "valid_macro_f1",
        "valid_raw_ece",
        "accuracy",
        "macro_f1",
        "normal_fpr",
        "temperature",
        "valid_nll",
        "raw_ece",
        "raw_brier",
        "raw_mean_confidence",
        "temp_ece",
        "temp_brier",
        "temp_mean_confidence",
        "group2_temp_ece",
        "group2_temp_brier",
        "group2_temp_mean_confidence",
        "group3_temp_ece",
        "group3_temp_brier",
        "group3_temp_mean_confidence",
        "group2_temperatures",
        "group3_temperatures",
        "inference_latency_ms_per_1k",
        "train_rows",
        "valid_rows",
        "test_rows",
        "n_features",
    ]
    with (out_dir / "cti_v08_posthoc_calibration_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        for row in rows:
            writer.writerow({col: row.get(col, "") for col in cols})
    (out_dir / "cti_v08_posthoc_calibration_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# CTI v0.8 Post-hoc Calibration Summary",
        "",
        "This probe keeps the v0.7 classifier/alpha-selection protocol and adds validation-only source-gate-binned temperature scaling. Macro-F1 is based on raw logits; temperature scaling only changes calibration metrics.",
        "",
        "| Scenario | Seed | Alpha | Macro-F1 | Normal FPR | Raw ECE | Scalar ECE | Group2 ECE | Group3 ECE | Scalar Brier | Group2 Brier | Group3 Brier |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['scenario']} | {row['seed']} | {row['selected_alpha']:.2f} | "
            f"{row['macro_f1']:.4f} | {row['normal_fpr']:.4f} | "
            f"{row['raw_ece']:.4f} | {row['temp_ece']:.4f} | {row['group2_temp_ece']:.4f} | {row['group3_temp_ece']:.4f} | "
            f"{row['temp_brier']:.4f} | {row['group2_temp_brier']:.4f} | {row['group3_temp_brier']:.4f} |"
        )
    (out_dir / "cti_v08_posthoc_calibration_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-data", default=None)
    parser.add_argument("--test-data", default=None)
    parser.add_argument("--dataset-name", default="unsw_nb15")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--valid-ratio", type=float, default=0.20)
    parser.add_argument("--epochs", type=int, default=80)
    parser.add_argument("--batch-size", type=int, default=2048)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--max-cat-unique", type=int, default=80)
    parser.add_argument("--label-smoothing", type=float, default=0.05)
    parser.add_argument("--confidence-penalty", type=float, default=0.01)
    parser.add_argument("--ece-penalty", type=float, default=0.75)
    parser.add_argument("--brier-penalty", type=float, default=0.10)
    parser.add_argument("--min-group-size", type=int, default=50)
    parser.add_argument("--alpha-grid", nargs="+", type=float, default=[0.0, 0.25, 0.50, 0.75, 1.0, 1.25])
    parser.add_argument("--alpha-f1-abs-tolerance", type=float, default=0.010)
    parser.add_argument("--alpha-f1-rel-tolerance", type=float, default=0.025)
    parser.add_argument("--max-train-rows", type=int, default=0)
    parser.add_argument("--max-valid-rows", type=int, default=0)
    parser.add_argument("--max-test-rows", type=int, default=0)
    parser.add_argument("--seeds", nargs="+", type=int, default=[42, 43, 44])
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["traffic_only", "source_gate", "cal_source_gate", "cal_source_gate_ece", "random_cti", "cal_random_source_gate", "cal_random_source_gate_ece"],
        choices=[
            "traffic_only",
            "weak_cti_concat",
            "source_gate",
            "source_gate_pruned",
            "cal_source_gate",
            "cal_source_gate_ece",
            "random_cti",
            "random_source_gate",
            "cal_random_source_gate",
            "cal_random_source_gate_ece",
        ],
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    train_path = find_parquet("UNSW_NB15_training-set.parquet", args.train_data)
    test_path = find_parquet("UNSW_NB15_testing-set.parquet", args.test_data)
    train_all = read_table(train_path)
    test_raw = read_table(test_path)
    manifest = {
        "train_path": str(train_path),
        "test_path": str(test_path),
        "train_rows": int(len(train_all)),
        "test_rows": int(len(test_raw)),
        "train_label_counts": {k: int(v) for k, v in train_all["_family_label"].value_counts().sort_index().items()},
        "test_label_counts": {k: int(v) for k, v in test_raw["_family_label"].value_counts().sort_index().items()},
        "validation_ratio": args.valid_ratio,
        "alpha_grid": [float(x) for x in args.alpha_grid],
        "label_smoothing": args.label_smoothing,
        "confidence_penalty": args.confidence_penalty,
        "ece_penalty": args.ece_penalty,
        "brier_penalty": args.brier_penalty,
        "min_group_size": args.min_group_size,
        "row_caps": {
            "max_train_rows": args.max_train_rows,
            "max_valid_rows": args.max_valid_rows,
            "max_test_rows": args.max_test_rows,
        },
        "protocol": "official train/test split; train partition split into train_core/validation for post-standardization CTI alpha selection, calibration-objective selection, scalar temperature scaling, and source-gate-binned temperature scaling",
    }
    rows: list[dict[str, Any]] = []
    for seed in args.seeds:
        for mode in args.modes:
            rows.append(run_one(train_all, test_raw, args, mode, seed))
    write_summary(rows, manifest, Path(args.out_dir))


if __name__ == "__main__":
    main()
