#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from train_baseline import main


def find_clean_file() -> str:
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


def run_one(data_path: str, cfg: dict[str, object]) -> None:
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
    data_path = find_clean_file()
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
        run_one(data_path, cfg)


if __name__ == "__main__":
    main_matrix()
