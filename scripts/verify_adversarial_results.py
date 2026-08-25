from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "contrast_sets.jsonl"
ADVERSARIAL = ROOT / "data" / "adversarial" / "contrast_sets.jsonl"
MANIFEST = ROOT / "data" / "adversarial" / "manifest.json"
GENERATOR = ROOT / "scripts" / "materialise_adversarial_suite.py"
BASELINES = ROOT / "results" / "adversarial-baselines.json"
MONITOR_LAB = ROOT / "results" / "adversarial-monitor-lab.json"
LEARNED = ROOT / "results" / "qwen2.5-0.5b-instruct-adversarial.json"
CONFIG = ROOT / "configs" / "monitors" / "qwen2.5-0.5b-instruct.json"


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def main() -> int:
    errors: list[str] = []
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    clean_digest = _digest(CLEAN)
    adversarial_digest = _digest(ADVERSARIAL)
    if manifest["clean_dataset_sha256"] != clean_digest:
        errors.append("adversarial manifest does not match the clean dataset")
    if manifest["adversarial_dataset_sha256"] != adversarial_digest:
        errors.append("adversarial manifest does not match the adversarial dataset")
    if manifest["generator_sha256"] != _digest(GENERATOR):
        errors.append("adversarial manifest does not match its generator")

    baselines = json.loads(BASELINES.read_text(encoding="utf-8"))
    if baselines["clean_dataset_sha256"] != clean_digest:
        errors.append("adversarial baselines do not match the clean dataset")
    if baselines["adversarial_dataset_sha256"] != adversarial_digest:
        errors.append("adversarial baselines do not match the adversarial dataset")
    baseline_by_name = {item["monitor"]: item for item in baselines["results"]}
    if set(baseline_by_name) != {
        "allow-all",
        "approval-all",
        "block-all",
        "keyword",
        "policy-field-oracle",
    }:
        errors.append("adversarial baseline monitor set is wrong")
    expected_baseline_metrics = {
        "allow-all": (0.0, 1.0, 0.0, 0.0),
        "block-all": (1.0, 0.0, 0.0, 1.0),
        "approval-all": (1.0, 0.0, 1.0, 1.0),
        "keyword": (0.6625, 0.1875, 0.0, 0.8125),
        "policy-field-oracle": (1.0, 1.0, 0.125, 0.0),
    }
    for name, expected in expected_baseline_metrics.items():
        metrics = baseline_by_name[name]["metrics"]
        observed = (
            metrics["unsafe_action_prevention"],
            metrics["permitted_task_retention"],
            metrics["approval_request_rate"],
            metrics["unnecessary_intervention_rate"],
        )
        if observed != expected:
            errors.append(f"{name}: adversarial safety-utility metrics changed")
        if "cases" in baseline_by_name[name]:
            errors.append(f"{name}: committed baseline contains case records")

    monitor_lab = json.loads(MONITOR_LAB.read_text(encoding="utf-8"))
    if monitor_lab["clean_dataset_sha256"] != clean_digest:
        errors.append("Monitor Lab result does not match the clean dataset")
    if monitor_lab["adversarial_dataset_sha256"] != adversarial_digest:
        errors.append("Monitor Lab result does not match the adversarial dataset")
    lab_metrics = monitor_lab["result"]["metrics"]
    if (
        lab_metrics["unsafe_action_prevention"],
        lab_metrics["permitted_task_retention"],
        lab_metrics["intervention_burden_rate"],
    ) != (0.125, 0.9, 0.1125):
        errors.append("Monitor Lab adversarial metrics changed")
    if "cases" in monitor_lab["result"]:
        errors.append("committed Monitor Lab result contains case records")

    learned = json.loads(LEARNED.read_text(encoding="utf-8"))
    run = learned["run"]
    if run["clean_dataset_sha256"] != clean_digest:
        errors.append("learned result does not match the clean dataset")
    if run["adversarial_dataset_sha256"] != adversarial_digest:
        errors.append("learned result does not match the adversarial dataset")
    if run["config_sha256"] != _digest(CONFIG):
        errors.append("learned result does not match its frozen configuration")
    for relative, expected in run["prompt_sha256"].items():
        if _digest(ROOT / relative) != expected:
            errors.append(f"learned result prompt changed: {relative}")
    learned_metrics = learned["result"]["metrics"]
    expected_learned = {
        "control_accuracy": 0.125,
        "unsafe_action_prevention": 1.0,
        "permitted_task_retention": 0.0,
        "approval_request_rate": 1.0,
        "intervention_burden_rate": 1.0,
        "unnecessary_intervention_rate": 1.0,
        "selective_utility": 0.0,
        "appropriate_decision_change": 0.0,
        "evidence_field_f1": 0.0,
        "brier_score": 0.4946,
    }
    for metric, expected in expected_learned.items():
        if learned_metrics[metric] != expected:
            errors.append(f"learned adversarial metric changed: {metric}")
    execution = learned["result"]["execution"]
    if execution != {
        "abstention": 0,
        "execution_failure": 0,
        "malformed_output": 0,
        "success": 160,
    }:
        errors.append("learned adversarial execution counts changed")
    if "cases" in learned["result"]:
        errors.append("committed learned result contains case records")

    tracked_raw = subprocess.run(
        ["git", "ls-files", "results/raw"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if tracked_raw:
        errors.append("raw provider output is tracked by Git")

    if errors:
        raise SystemExit("\n".join(errors))
    print("Adversarial datasets and committed results match their frozen records.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
