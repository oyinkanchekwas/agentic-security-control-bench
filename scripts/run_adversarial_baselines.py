from __future__ import annotations

import argparse
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
from control_bench.dataset import load_contrast_sets
from control_bench.monitors import ApprovalMonitor, MONITORS


ROOT = Path(__file__).resolve().parents[1]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
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
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "results" / "adversarial-baselines.json",
    )
    parser.add_argument("--bootstrap-iterations", type=int, default=1000)
    parser.add_argument("--bootstrap-seed", type=int, default=20260825)
    return parser


def main() -> int:
    args = build_parser().parse_args()
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
    monitors = [
        MONITORS["allow-all"],
        MONITORS["block-all"],
        ApprovalMonitor(),
        MONITORS["keyword"],
        MONITORS["policy-field-oracle"],
    ]
    results = [
        evaluate_adversarial_monitor(
            monitor,
            clean_sets,
            adversarial_sets,
            bootstrap_iterations=args.bootstrap_iterations,
            bootstrap_seed=args.bootstrap_seed,
        )
        for monitor in monitors
    ]
    payload = {
        "adversarial_suite": str(args.adversarial.relative_to(ROOT)),
        "adversarial_dataset_sha256": sha256(args.adversarial.read_bytes()).hexdigest(),
        "clean_dataset": str(args.clean.relative_to(ROOT)),
        "clean_dataset_sha256": clean_digest,
        "bootstrap_iterations": args.bootstrap_iterations,
        "bootstrap_seed": args.bootstrap_seed,
        "results": [without_cases(item) for item in results],
        "paired_comparisons": paired_adversarial_comparisons(
            results,
            iterations=args.bootstrap_iterations,
            seed=args.bootstrap_seed,
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
