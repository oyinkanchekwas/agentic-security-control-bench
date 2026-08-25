from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from control_bench.configuration import (
    build_configured_monitor,
    load_run_config,
    prompt_paths,
)
from control_bench.dataset import load_contrast_sets, validate_contrast_sets
from control_bench.evaluation import evaluate_monitor, paired_bootstrap_comparisons
from control_bench.monitors import MONITORS


ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a configured model monitor")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "contrast_sets.jsonl")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--raw-out", type=Path, required=True)
    parser.add_argument("--bootstrap-iterations", type=int, default=1000)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_run_config(args.config)
    contrast_sets = load_contrast_sets(args.dataset)
    errors = validate_contrast_sets(contrast_sets)
    if errors:
        raise ValueError("dataset validation failed: " + "; ".join(errors))
    selected = tuple(item for item in contrast_sets if item.split == config["split"])
    monitor = build_configured_monitor(config, ROOT)
    result = evaluate_monitor(
        monitor,
        selected,
        bootstrap_iterations=args.bootstrap_iterations,
        bootstrap_seed=int(config.get("bootstrap_seed", 20260825)),
    )
    comparison_result = evaluate_monitor(
        MONITORS["keyword"],
        selected,
        bootstrap_iterations=args.bootstrap_iterations,
        bootstrap_seed=int(config.get("bootstrap_seed", 20260825)),
    )
    paired = paired_bootstrap_comparisons(
        [result, comparison_result],
        iterations=args.bootstrap_iterations,
        seed=int(config.get("bootstrap_seed", 20260825)),
    )
    config_bytes = args.config.read_bytes()
    dataset_digest = sha256(args.dataset.read_bytes()).hexdigest()
    prompts = {
        path.relative_to(ROOT).as_posix(): sha256(path.read_bytes()).hexdigest()
        for path in prompt_paths(config, ROOT)
    }
    payload = {
        "run": {
            "monitor": config["name"],
            "monitor_kind": config["monitor_kind"],
            "provider": config["provider"]["kind"],
            "model_id": config["provider"]["model_id"],
            "model_revision": config["provider"].get("revision"),
            "prompt_version": config["prompt_version"],
            "prompt_sha256": prompts,
            "temperature": config.get("temperature", 0.0),
            "seed": config.get("seed"),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "dataset_split": config["split"],
            "dataset_sha256": dataset_digest,
            "config_sha256": sha256(config_bytes).hexdigest(),
        },
        "result": _without_cases(result),
        "paired_comparisons": paired,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raw_records = _raw_records(monitor)
    args.raw_out.parent.mkdir(parents=True, exist_ok=True)
    args.raw_out.write_text(
        "".join(json.dumps(record, sort_keys=True) + "\n" for record in raw_records),
        encoding="utf-8",
    )
    print(f"Wrote summary to {args.out}")
    print(f"Wrote {len(raw_records)} raw provider records to {args.raw_out}")
    return 0


def _without_cases(result: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in result.items() if key != "cases"}


def _raw_records(monitor) -> list[dict[str, object]]:
    if hasattr(monitor, "raw_records"):
        return list(monitor.raw_records)
    learned = getattr(monitor, "learned", None)
    return list(getattr(learned, "raw_records", []))


if __name__ == "__main__":
    raise SystemExit(main())
