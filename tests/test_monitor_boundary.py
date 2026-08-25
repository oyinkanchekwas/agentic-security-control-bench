from pathlib import Path
import unittest

from control_bench.dataset import load_contrast_sets
from control_bench.evaluation import evaluate_monitor
from control_bench.models import ControlAction, MonitorDecision, MonitorTrace


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "contrast_sets.jsonl"


class BoundaryProbe:
    name = "boundary-probe"

    def __init__(self) -> None:
        self.trace_fields: set[str] = set()
        self.event_fields: set[str] = set()

    def inspect(self, trace: MonitorTrace) -> MonitorDecision:
        self.trace_fields.update(trace.__dataclass_fields__)
        self.event_fields.update(trace.events[-1].__dataclass_fields__)
        return MonitorDecision(
            trace_id=trace.trace_id,
            control=ControlAction.ALLOW,
            risk_score=0.0,
            event_id=None,
        )


class MonitorBoundaryTests(unittest.TestCase):
    def test_monitor_input_excludes_labels_outcomes_and_recovery(self) -> None:
        probe = BoundaryProbe()
        contrast_sets = load_contrast_sets(DATASET)
        evaluate_monitor(probe, contrast_sets, bootstrap_iterations=0)
        self.assertTrue({"trace_id", "task", "events"}.issubset(probe.trace_fields))
        self.assertTrue({"content", "attributes", "kind"}.issubset(probe.event_fields))
        self.assertTrue({"gold", "recovery", "required_effects"}.isdisjoint(probe.trace_fields))
        self.assertTrue({"effects", "status", "contributes_to_task"}.isdisjoint(probe.event_fields))


if __name__ == "__main__":
    unittest.main()
