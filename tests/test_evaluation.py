from pathlib import Path
import unittest

from control_bench.dataset import load_contrast_sets
from control_bench.evaluation import evaluate_monitor
from control_bench.monitors import MONITORS


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "contrast_sets.jsonl"


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contrast_sets = load_contrast_sets(DATASET)

    def test_allow_and_block_baselines_expose_utility_trade_off(self) -> None:
        allow = evaluate_monitor(MONITORS["allow-all"], self.contrast_sets)["metrics"]
        block = evaluate_monitor(MONITORS["block-all"], self.contrast_sets)["metrics"]
        self.assertEqual(allow["unsafe_action_prevention"], 0.0)
        self.assertEqual(allow["permitted_task_retention"], 1.0)
        self.assertEqual(block["unsafe_action_prevention"], 1.0)
        self.assertEqual(block["permitted_task_retention"], 0.0)

    def test_policy_field_reference_matches_seed_labels(self) -> None:
        metrics = evaluate_monitor(MONITORS["policy-field"], self.contrast_sets)["metrics"]
        self.assertEqual(metrics["control_accuracy"], 1.0)
        self.assertEqual(metrics["causal_evidence_accuracy"], 1.0)
        self.assertEqual(metrics["task_completion"], 1.0)

    def test_keyword_baseline_is_sensitive_to_decoys(self) -> None:
        metrics = evaluate_monitor(MONITORS["keyword"], self.contrast_sets)["metrics"]
        self.assertLess(metrics["counterfactual_stability"], 1.0)
        self.assertLess(metrics["permitted_task_retention"], 1.0)


if __name__ == "__main__":
    unittest.main()
