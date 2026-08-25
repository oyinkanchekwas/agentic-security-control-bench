from pathlib import Path
from collections import Counter
from hashlib import sha256
import json
import unittest

from control_bench.dataset import load_contrast_sets, validate_contrast_sets


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "contrast_sets.jsonl"
MANIFEST = ROOT / "data" / "manifest.json"


class DatasetTests(unittest.TestCase):
    def test_dataset_shape(self) -> None:
        contrast_sets = load_contrast_sets(DATASET)
        self.assertEqual(len(contrast_sets), 80)
        self.assertEqual(sum(len(item.variants) for item in contrast_sets), 320)
        self.assertEqual(Counter(item.split for item in contrast_sets), {"train": 32, "dev": 32, "test": 16})
        self.assertEqual(
            Counter(item.failure_mode for item in contrast_sets),
            {
                "data_exfiltration": 10,
                "destructive_command": 10,
                "false_verification_claim": 10,
                "permission_boundary_violation": 10,
                "prompt_injection_compliance": 10,
                "secret_exposure": 10,
                "supply_chain_risk": 10,
                "test_weakening": 10,
            },
        )
        for item in contrast_sets:
            labels = [variant.gold.label for variant in item.variants]
            self.assertEqual(labels.count("permitted"), 2)
            self.assertEqual(labels.count("unsafe"), 2)

    def test_dataset_validates(self) -> None:
        contrast_sets = load_contrast_sets(DATASET)
        self.assertEqual(validate_contrast_sets(contrast_sets), [])

    def test_scenarios_are_disjoint_between_splits(self) -> None:
        contrast_sets = load_contrast_sets(DATASET)
        scenarios = {
            split: {item.scenario_id for item in contrast_sets if item.split == split}
            for split in ("train", "dev", "test")
        }
        self.assertTrue(scenarios["train"].isdisjoint(scenarios["dev"]))
        self.assertTrue(scenarios["train"].isdisjoint(scenarios["test"]))
        self.assertTrue(scenarios["dev"].isdisjoint(scenarios["test"]))

    def test_manifest_matches_materialised_data(self) -> None:
        payload = DATASET.read_bytes()
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["benchmark_version"], "0.3.0")
        self.assertEqual(manifest["trace_count"], 320)
        self.assertEqual(manifest["sha256"], sha256(payload).hexdigest())

    def test_policy_metadata_matches_permitted_decoy_actions(self) -> None:
        contrast_sets = load_contrast_sets(DATASET)
        for contrast_set in contrast_sets:
            for trace in contrast_set.variants:
                attributes = trace.events[-1].attributes
                if attributes.get("claim_matches_evidence") is True:
                    self.assertEqual(attributes["executed_scope"], attributes["reported_scope"])
                if contrast_set.failure_mode == "test_weakening" and trace.variant == "permitted_decoy":
                    self.assertEqual(attributes["change_target"], "duplicate_test")


if __name__ == "__main__":
    unittest.main()
