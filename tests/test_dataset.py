from pathlib import Path
import unittest

from control_bench.dataset import load_contrast_sets, validate_contrast_sets


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "contrast_sets.jsonl"


class DatasetTests(unittest.TestCase):
    def test_seed_dataset_shape(self) -> None:
        contrast_sets = load_contrast_sets(DATASET)
        self.assertEqual(len(contrast_sets), 8)
        self.assertEqual(sum(len(item.variants) for item in contrast_sets), 32)
        for item in contrast_sets:
            labels = [variant.gold.label for variant in item.variants]
            self.assertEqual(labels.count("permitted"), 2)
            self.assertEqual(labels.count("unsafe"), 2)

    def test_seed_dataset_validates(self) -> None:
        contrast_sets = load_contrast_sets(DATASET)
        self.assertEqual(validate_contrast_sets(contrast_sets), [])


if __name__ == "__main__":
    unittest.main()
