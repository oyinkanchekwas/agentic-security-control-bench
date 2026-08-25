from pathlib import Path
import unittest

from control_bench.dataset import load_contrast_sets
from control_bench.models import ControlAction
from control_bench.replay import replay_trace


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "contrast_sets.jsonl"


class ReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.traces = [
            variant
            for contrast_set in load_contrast_sets(DATASET)
            for variant in contrast_set.variants
        ]

    def test_gold_controls_preserve_task_without_harm(self) -> None:
        for trace in self.traces:
            with self.subTest(trace=trace.trace_id):
                outcome = replay_trace(trace, trace.gold.control)
                self.assertFalse(outcome.harm)
                self.assertTrue(outcome.task_complete)

    def test_allow_exposes_every_unsafe_variant(self) -> None:
        unsafe = [trace for trace in self.traces if trace.gold.label == "unsafe"]
        for trace in unsafe:
            with self.subTest(trace=trace.trace_id):
                self.assertTrue(replay_trace(trace, ControlAction.ALLOW).harm)


if __name__ == "__main__":
    unittest.main()
