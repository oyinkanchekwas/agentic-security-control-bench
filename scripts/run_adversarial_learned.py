from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from control_bench.adversarial import (
    clean_dataset_digest,
    load_adversarial_sets,
    validate_adversarial_sets,
)
from control_bench.adversarial_evaluation import (
    evaluate_adversarial_monitor,
    paired_adversarial_comparisons,
    without_cases,
)
from control_bench.configuration import build_configured_monitor, load_run_config, prompt_paths
from control_bench.dataset import load_contrast_sets
from control_bench.monitors import ApprovalMonitor, MONITORS


ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a configured monitor on the adversarial suite")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument(
        "--clean",
        type=Path,
        default=ROOT / "data" / "contrast_sets.jsonl",
    )
    parser.add_argument(
        "--adversarial",
        type=Path,
        default=ROOT / "data" / "adversarial" / "contrast_sets.jsonl",
    )
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--raw-out", type=Path, required=True)
    parser.add_argument("--bootstrap-iterations", type=int, default=1000)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    config = load_run_config(args.config)
    clean_sets = load_contrast_sets(args.clean)
    adversarial_sets = load_adversarial_sets(args.adversarial)
    clean_digest = clean_dataset_digest(args.clean)
    errors = validate_adversarial_sets(
        adversarial_sets,
        clean_sets,
        clean_digest=clean_digest,
    )
    if errors:
        raise SystemExit("\n".join(errors))

    monitor = build_configured_monitor(config, ROOT)
    seed = int(config.get("bootstrap_seed", 20260825))
    learned_result = evaluate_adversarial_monitor(
        monitor,
        clean_sets,
        adversarial_sets,
        bootstrap_iterations=args.bootstrap_iterations,
        bootstrap_seed=seed,
    )
    fixed_monitors = [
        MONITORS["allow-all"],
        MONITORS["block-all"],
        ApprovalMonitor(),
        MONITORS["keyword"],
    ]
    fixed_results = [
        evaluate_adversarial_monitor(
            fixed_monitor,
            clean_sets,
            adversarial_sets,
            bootstrap_iterations=args.bootstrap_iterations,
            bootstrap_seed=seed,
        )
        for fixed_monitor in fixed_monitors
    ]
    config_bytes = args.config.read_bytes()
    prompt_digests = {
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
            "prompt_sha256": prompt_digests,
            "temperature": config.get("temperature", 0.0),
            "seed": config.get("seed"),
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "partition": "adversarial_holdout",
            "clean_dataset_sha256": clean_digest,
            "adversarial_dataset_sha256": sha256(args.adversarial.read_bytes()).hexdigest(),
            "config_sha256": sha256(config_bytes).hexdigest(),
        },
        "result": without_cases(learned_result),
        "paired_comparisons": [
            item
            for item in paired_adversarial_comparisons(
                [learned_result, *fixed_results],
                iterations=args.bootstrap_iterations,
                seed=seed,
            )
            if config["name"] in {item["left_monitor"], item["right_monitor"]}
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    raw_records = _raw_records(monitor)
    args.raw_out.parent.mkdir(parents=True, exist_ok=True)
    args.raw_out.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in raw_records),
        encoding="utf-8",
    )
    print(f"Wrote summary to {args.out}")
    print(f"Wrote {len(raw_records)} raw provider records to {args.raw_out}")
    return 0


def _raw_records(monitor) -> list[dict[str, object]]:
    if hasattr(monitor, "raw_records"):
        return list(monitor.raw_records)
    learned = getattr(monitor, "learned", None)
    return list(getattr(learned, "raw_records", []))


if __name__ == "__main__":
    raise SystemExit(main())
