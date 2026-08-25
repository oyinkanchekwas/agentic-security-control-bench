from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results" / "qwen2.5-0.5b-instruct-test.json"
CONFIG = ROOT / "configs" / "monitors" / "qwen2.5-0.5b-instruct.json"
MANIFEST = ROOT / "data" / "manifest.json"

REQUIRED_METRICS = {
    "control_accuracy",
    "unsafe_action_prevention",
    "permitted_task_retention",
    "intervention_event_accuracy",
    "evidence_field_precision",
    "evidence_field_recall",
    "evidence_field_f1",
    "causal_evidence_accuracy",
    "counterfactual_sensitivity",
    "counterfactual_stability",
    "replayed_task_completion",
    "brier_score",
    "mean_latency_ms",
    "total_tokens",
    "estimated_cost_usd",
    "abstention_rate",
    "malformed_output_rate",
    "execution_failure_rate",
}


def main() -> int:
    payload = json.loads(RESULT.read_text(encoding="utf-8"))
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    run = payload["run"]
    result = payload["result"]
    errors: list[str] = []
    if run["dataset_sha256"] != manifest["sha256"]:
        errors.append("learned result does not match the dataset digest")
    if run["config_sha256"] != sha256(CONFIG.read_bytes()).hexdigest():
        errors.append("learned result does not match the frozen configuration")
    if run["model_id"] != config["provider"]["model_id"]:
        errors.append("learned result model identifier differs from its configuration")
    if run["model_revision"] != config["provider"]["revision"]:
        errors.append("learned result model revision differs from its configuration")
    for relative, expected in run["prompt_sha256"].items():
        observed = sha256((ROOT / relative).read_bytes()).hexdigest()
        if observed != expected:
            errors.append(f"learned result prompt digest changed: {relative}")
    if result["benchmark_version"] != "0.3.0":
        errors.append("learned result benchmark version is not 0.3.0")
    if result["case_count"] != 64 or result["contrast_set_count"] != 16:
        errors.append("learned result does not cover all held-out test cases")
    if set(result["by_split"]) != {"test"}:
        errors.append("learned result contains an unexpected split")
    if len(result["by_policy_family"]) != 8:
        errors.append("learned result is missing policy-family reports")
    if not REQUIRED_METRICS.issubset(result["metrics"]):
        errors.append("learned result is missing required measures")
    if "cases" in result:
        errors.append("case-level provider results are present in the committed summary")
    if sum(result["execution"].values()) != 64:
        errors.append("learned result execution counts do not sum to 64")
    if not payload.get("paired_comparisons"):
        errors.append("learned result is missing a paired comparison")
    if "provider_response" in json.dumps(payload):
        errors.append("raw provider responses are present in the committed summary")
    if errors:
        print("\n".join(errors))
        return 1
    print("Held-out learned result matches its dataset, prompts, and frozen configuration.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
