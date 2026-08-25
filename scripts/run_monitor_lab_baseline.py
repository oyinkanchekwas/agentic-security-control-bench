from __future__ import annotations

import argparse
import json
from pathlib import Path

from control_bench.dataset import load_contrast_sets, validate_contrast_sets
from control_bench.evaluation import evaluate_monitor
from control_bench.monitor_lab_adapter import MonitorLabAdapter


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=ROOT / "data" / "contrast_sets.jsonl")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "monitor_lab.json")
    args = parser.parse_args()

    contrast_sets = load_contrast_sets(args.dataset)
    errors = validate_contrast_sets(contrast_sets)
    if errors:
        print("\n".join(errors))
        return 1

    lock = json.loads((ROOT / "programme-lock.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "data" / "manifest.json").read_text(encoding="utf-8"))
    result = evaluate_monitor(MonitorLabAdapter(), contrast_sets)
    result.pop("cases", None)
    payload = {
        "dataset": {
            "benchmark_version": manifest["benchmark_version"],
            "sha256": manifest["sha256"],
        },
        "source": lock["coding_agent_monitor_lab"],
        "result": result,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
