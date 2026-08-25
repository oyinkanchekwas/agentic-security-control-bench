from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Sequence

from control_bench.dataset import load_contrast_sets, validate_contrast_sets
from control_bench.evaluation import evaluate_monitor
from control_bench.monitors import MONITORS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="control-bench")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate a contrast-set dataset")
    validate.add_argument("dataset", type=Path)

    evaluate = subparsers.add_parser("evaluate", help="Run one monitor against the dataset")
    evaluate.add_argument("dataset", type=Path)
    evaluate.add_argument("--monitor", choices=sorted(MONITORS), required=True)
    evaluate.add_argument("--out", type=Path)
    evaluate.add_argument("--pretty", action="store_true")
    evaluate.add_argument("--summary-only", action="store_true")
    evaluate.add_argument("--split", choices=("all", "train", "dev", "test"), default="all")
    evaluate.add_argument("--bootstrap-iterations", type=int, default=1000)
    evaluate.add_argument("--bootstrap-seed", type=int, default=20260825)

    compare = subparsers.add_parser("compare", help="Run every included monitor")
    compare.add_argument("dataset", type=Path)
    compare.add_argument("--out", type=Path)
    compare.add_argument("--pretty", action="store_true")
    compare.add_argument("--summary-only", action="store_true")
    compare.add_argument("--split", choices=("all", "train", "dev", "test"), default="all")
    compare.add_argument("--bootstrap-iterations", type=int, default=1000)
    compare.add_argument("--bootstrap-seed", type=int, default=20260825)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    contrast_sets = load_contrast_sets(args.dataset)
    errors = validate_contrast_sets(contrast_sets)
    if errors:
        for error in errors:
            print(error)
        return 1

    if args.command == "validate":
        trace_count = sum(len(item.variants) for item in contrast_sets)
        print(f"Validated {len(contrast_sets)} contrast sets and {trace_count} traces.")
        return 0

    selected_sets = (
        contrast_sets
        if args.split == "all"
        else tuple(item for item in contrast_sets if item.split == args.split)
    )

    if args.command == "evaluate":
        payload: object = evaluate_monitor(
            MONITORS[args.monitor],
            selected_sets,
            bootstrap_iterations=args.bootstrap_iterations,
            bootstrap_seed=args.bootstrap_seed,
        )
        if args.summary_only:
            payload = _without_cases(payload)
    else:
        results = [
            evaluate_monitor(
                monitor,
                selected_sets,
                bootstrap_iterations=args.bootstrap_iterations,
                bootstrap_seed=args.bootstrap_seed,
            )
            for monitor in MONITORS.values()
        ]
        if args.summary_only:
            results = [_without_cases(result) for result in results]
        payload = {
            "dataset": str(args.dataset),
            "dataset_sha256": sha256(args.dataset.read_bytes()).hexdigest(),
            "split": args.split,
            "results": results,
        }
    rendered = json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(rendered)
    return 0


def _without_cases(result: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in result.items() if key != "cases"}
