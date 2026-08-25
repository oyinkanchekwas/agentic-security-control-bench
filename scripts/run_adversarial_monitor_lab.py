from __future__ import annotations

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
from control_bench.monitor_lab_adapter import MonitorLabAdapter
from control_bench.monitors import ApprovalMonitor, MONITORS


ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "contrast_sets.jsonl"
ADVERSARIAL = ROOT / "data" / "adversarial" / "contrast_sets.jsonl"
OUTPUT = ROOT / "results" / "adversarial-monitor-lab.json"


def main() -> int:
    clean_sets = load_contrast_sets(CLEAN)
    adversarial_sets = load_adversarial_sets(ADVERSARIAL)
    clean_digest = clean_dataset_digest(CLEAN)
    errors = validate_adversarial_sets(
        adversarial_sets,
        clean_sets,
        clean_digest=clean_digest,
    )
    if errors:
        raise SystemExit("\n".join(errors))
    monitor_lab = evaluate_adversarial_monitor(
        MonitorLabAdapter(), clean_sets, adversarial_sets
    )
    comparison_monitors = [
        MONITORS["allow-all"],
        MONITORS["block-all"],
        ApprovalMonitor(),
        MONITORS["keyword"],
    ]
    comparison_results = [
        evaluate_adversarial_monitor(monitor, clean_sets, adversarial_sets)
        for monitor in comparison_monitors
    ]
    payload = {
        "adversarial_dataset_sha256": sha256(ADVERSARIAL.read_bytes()).hexdigest(),
        "clean_dataset_sha256": clean_digest,
        "result": without_cases(monitor_lab),
        "paired_comparisons": [
            item
            for item in paired_adversarial_comparisons(
                [monitor_lab, *comparison_results]
            )
            if "monitor-lab" in {item["left_monitor"], item["right_monitor"]}
        ],
    }
    OUTPUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
