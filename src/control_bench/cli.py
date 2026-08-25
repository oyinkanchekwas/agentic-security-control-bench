from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
from typing import Sequence

from control_bench.adversarial import (
    clean_dataset_digest,
    load_adversarial_sets,
    validate_adversarial_sets,
)
from control_bench.adversarial_evaluation import (
    evaluate_adversarial_monitor,
    paired_adversarial_comparisons,
)
from control_bench.dataset import load_contrast_sets, validate_contrast_sets
from control_bench.evaluation import evaluate_monitor, paired_bootstrap_comparisons
from control_bench.monitors import ApprovalMonitor, MONITORS


ADVERSARIAL_MONITORS = {**MONITORS, "approval-all": ApprovalMonitor()}


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

    validate_adversarial = subparsers.add_parser(
        "validate-adversarial",
        help="Validate the adversarial suite against its frozen clean dataset",
    )
    validate_adversarial.add_argument("dataset", type=Path)
    validate_adversarial.add_argument("--clean", type=Path, required=True)

    evaluate_adversarial = subparsers.add_parser(
        "evaluate-adversarial",
        help="Run one included monitor against the adversarial suite",
    )
    evaluate_adversarial.add_argument("dataset", type=Path)
    evaluate_adversarial.add_argument("--clean", type=Path, required=True)
    evaluate_adversarial.add_argument(
        "--monitor", choices=sorted(ADVERSARIAL_MONITORS), required=True
    )
    evaluate_adversarial.add_argument("--out", type=Path)
    evaluate_adversarial.add_argument("--pretty", action="store_true")
    evaluate_adversarial.add_argument("--summary-only", action="store_true")
    evaluate_adversarial.add_argument("--bootstrap-iterations", type=int, default=1000)
    evaluate_adversarial.add_argument("--bootstrap-seed", type=int, default=20260825)

    compare_adversarial = subparsers.add_parser(
        "compare-adversarial",
        help="Run every included monitor against the adversarial suite",
    )
    compare_adversarial.add_argument("dataset", type=Path)
    compare_adversarial.add_argument("--clean", type=Path, required=True)
    compare_adversarial.add_argument("--out", type=Path)
    compare_adversarial.add_argument("--pretty", action="store_true")
    compare_adversarial.add_argument("--summary-only", action="store_true")
    compare_adversarial.add_argument("--bootstrap-iterations", type=int, default=1000)
    compare_adversarial.add_argument("--bootstrap-seed", type=int, default=20260825)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {
        "validate-adversarial",
        "evaluate-adversarial",
        "compare-adversarial",
    }:
        return _run_adversarial(args)
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
        paired = paired_bootstrap_comparisons(
            results,
            iterations=args.bootstrap_iterations,
            seed=args.bootstrap_seed,
        )
        if args.summary_only:
            results = [_without_cases(result) for result in results]
        payload = {
            "dataset": str(args.dataset),
            "dataset_sha256": sha256(args.dataset.read_bytes()).hexdigest(),
            "split": args.split,
            "results": results,
            "paired_comparisons": paired,
        }
    rendered = json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
    else:
        print(rendered)
    return 0


def _run_adversarial(args: argparse.Namespace) -> int:
    clean_sets = load_contrast_sets(args.clean)
    adversarial_sets = load_adversarial_sets(args.dataset)
    clean_digest = clean_dataset_digest(args.clean)
    errors = validate_adversarial_sets(
        adversarial_sets,
        clean_sets,
        clean_digest=clean_digest,
    )
    if errors:
        for error in errors:
            print(error)
        return 1
    if args.command == "validate-adversarial":
        trace_count = sum(len(item.traces) for item in adversarial_sets)
        print(
            f"Validated {len(adversarial_sets)} adversarial contrast sets and "
            f"{trace_count} traces."
        )
        return 0

    if args.command == "evaluate-adversarial":
        payload: object = evaluate_adversarial_monitor(
            ADVERSARIAL_MONITORS[args.monitor],
            clean_sets,
            adversarial_sets,
            bootstrap_iterations=args.bootstrap_iterations,
            bootstrap_seed=args.bootstrap_seed,
        )
        if args.summary_only:
            payload = _without_cases(payload)
    else:
        results = [
            evaluate_adversarial_monitor(
                monitor,
                clean_sets,
                adversarial_sets,
                bootstrap_iterations=args.bootstrap_iterations,
                bootstrap_seed=args.bootstrap_seed,
            )
            for monitor in ADVERSARIAL_MONITORS.values()
        ]
        paired = paired_adversarial_comparisons(
            results,
            iterations=args.bootstrap_iterations,
            seed=args.bootstrap_seed,
        )
        if args.summary_only:
            results = [_without_cases(item) for item in results]
        payload = {
            "clean_dataset": str(args.clean),
            "clean_dataset_sha256": clean_digest,
            "adversarial_dataset": str(args.dataset),
            "adversarial_dataset_sha256": sha256(args.dataset.read_bytes()).hexdigest(),
            "results": results,
            "paired_comparisons": paired,
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
