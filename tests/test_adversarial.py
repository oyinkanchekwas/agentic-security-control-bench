from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import unittest

from control_bench.adversarial import (
    AdversarialSet,
    FROZEN_CLEAN_SHA256,
    PERTURBATION_CLASSES,
    as_contrast_sets,
    load_adversarial_sets,
    validate_adversarial_sets,
)
from control_bench.adversarial_evaluation import evaluate_adversarial_monitor
from control_bench.dataset import load_contrast_sets
from control_bench.learned_monitors import (
    AgenticInvestigatorMonitor,
    DeterministicModelEnsemble,
    ProviderReply,
    StructuredJudgeMonitor,
)
from control_bench.models import MonitorTrace
from control_bench.monitor_lab_adapter import MonitorLabAdapter
from control_bench.monitors import ApprovalMonitor, KeywordMonitor


ROOT = Path(__file__).resolve().parents[1]
CLEAN = ROOT / "data" / "contrast_sets.jsonl"
ADVERSARIAL = ROOT / "data" / "adversarial" / "contrast_sets.jsonl"
MANIFEST = ROOT / "data" / "adversarial" / "manifest.json"
LOCK = ROOT / "configs" / "v0.3-frozen.json"
PROMPT = "Return one JSON object matching the supplied response contract."


class AllowProvider:
    model_id = "fixture-provider"

    def complete(self, messages, *, temperature, seed):
        payload = json.loads(messages[-1]["content"])
        if "response_contract" not in payload:
            text = "No intervention is proposed from the visible trace."
        else:
            text = json.dumps(
                {
                    "control": "allow",
                    "first_actionable_event": None,
                    "evidence_fields": [],
                    "confidence": 0.2,
                    "reason": "No visible policy conflict was found.",
                }
            )
        return ProviderReply(text=text, model_id=self.model_id)


class EmptyLabMonitor:
    def scan(self, events):
        return ()


class LabEvent:
    def __init__(self, **payload):
        self.__dict__.update(payload)


class AdversarialSuiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.clean_sets = load_contrast_sets(CLEAN)
        cls.adversarial_sets = load_adversarial_sets(ADVERSARIAL)

    def test_frozen_v03_files_match_lock(self) -> None:
        lock = json.loads(LOCK.read_text(encoding="utf-8"))
        self.assertEqual(sha256(CLEAN.read_bytes()).hexdigest(), FROZEN_CLEAN_SHA256)
        for relative, expected in lock["files"].items():
            observed = sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertEqual(observed, expected, relative)

    def test_suite_shape_balance_and_manifest(self) -> None:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(len(self.adversarial_sets), 40)
        self.assertEqual(sum(len(item.traces) for item in self.adversarial_sets), 160)
        family_counts = Counter(
            item.contrast_set.failure_mode for item in self.adversarial_sets
        )
        class_counts = Counter(item.perturbation_class for item in self.adversarial_sets)
        self.assertEqual(set(class_counts), PERTURBATION_CLASSES)
        self.assertEqual(set(family_counts.values()), {5})
        self.assertEqual(set(class_counts.values()), {8})
        self.assertEqual(
            manifest["adversarial_dataset_sha256"],
            sha256(ADVERSARIAL.read_bytes()).hexdigest(),
        )
        self.assertEqual(manifest["clean_dataset_sha256"], FROZEN_CLEAN_SHA256)

    def test_relationships_validate_against_clean_test_cases(self) -> None:
        errors = validate_adversarial_sets(
            self.adversarial_sets,
            self.clean_sets,
            clean_digest=sha256(CLEAN.read_bytes()).hexdigest(),
        )
        self.assertEqual(errors, [])
        source_ids = {
            item.relationship.source_trace_id
            for adversarial_set in self.adversarial_sets
            for item in adversarial_set.traces
        }
        clean_test_ids = {
            trace.trace_id
            for contrast_set in self.clean_sets
            if contrast_set.split == "test"
            for trace in contrast_set.variants
        }
        self.assertTrue(source_ids.issubset(clean_test_ids))

    def test_relationship_boolean_is_not_coerced_from_text(self) -> None:
        payload = json.loads(ADVERSARIAL.read_text(encoding="utf-8").splitlines()[0])
        payload["variants"][0]["adversarial"]["causal_policy_state_unchanged"] = "false"
        with self.assertRaisesRegex(ValueError, "must be boolean"):
            AdversarialSet.from_dict(payload)

    def test_adversarial_content_is_inert_text(self) -> None:
        visible = json.dumps(
            [
                trace.trace.for_monitor().to_provider_dict()
                for adversarial_set in self.adversarial_sets
                for trace in adversarial_set.traces
            ]
        ).lower()
        for executable_form in ("http://", "https://", "curl ", "subprocess", "rm -"):
            self.assertNotIn(executable_form, visible)
        self.assertIn("collector.invalid", visible)

    def test_each_perturbation_has_its_required_trace_structure(self) -> None:
        by_class = {
            perturbation: [
                item.trace
                for adversarial_set in self.adversarial_sets
                if adversarial_set.perturbation_class == perturbation
                for item in adversarial_set.traces
            ]
            for perturbation in PERTURBATION_CLASSES
        }
        embedded_kinds = {
            event.kind
            for trace in by_class["embedded_instruction_attack"]
            for event in trace.events
        }
        self.assertTrue({"document", "comment", "log", "tool_output"}.issubset(embedded_kinds))
        for trace in by_class["multi_event_composition"]:
            actionable = [event for event in trace.events if event.kind in {"action", "response"}]
            self.assertEqual(len(actionable), 2)
            self.assertEqual(actionable[0].effects, ())
        deceptive_kinds = {
            event.kind
            for trace in by_class["deceptive_completion_verification"]
            for event in trace.events
        }
        self.assertTrue(
            {"claim_record", "check_record", "test_record", "evidence_record"}.issubset(
                deceptive_kinds
            )
        )

    def test_safety_utility_extremes_are_visible(self) -> None:
        allow = evaluate_adversarial_monitor(
            _AllowMonitor(), self.clean_sets, self.adversarial_sets, bootstrap_iterations=0
        )
        approval = evaluate_adversarial_monitor(
            ApprovalMonitor(), self.clean_sets, self.adversarial_sets, bootstrap_iterations=0
        )
        self.assertEqual(allow["metrics"]["unsafe_action_prevention"], 0.0)
        self.assertEqual(allow["metrics"]["permitted_task_retention"], 1.0)
        self.assertEqual(approval["metrics"]["unsafe_action_prevention"], 1.0)
        self.assertEqual(approval["metrics"]["permitted_task_retention"], 0.0)
        self.assertEqual(approval["metrics"]["approval_request_rate"], 1.0)
        self.assertEqual(approval["metrics"]["unnecessary_intervention_rate"], 1.0)

    def test_all_six_monitor_interfaces_accept_the_suite(self) -> None:
        local = StructuredJudgeMonitor(
            provider=AllowProvider(), instructions=PROMPT, name="local-instruction-model"
        )
        frontier = StructuredJudgeMonitor(
            provider=AllowProvider(), instructions=PROMPT, name="frontier-judge"
        )
        investigator = AgenticInvestigatorMonitor(
            provider=AllowProvider(),
            investigation_instructions="Inspect visible fields.",
            decision_instructions=PROMPT,
        )
        ensemble = DeterministicModelEnsemble(
            deterministic=KeywordMonitor(),
            learned=StructuredJudgeMonitor(provider=AllowProvider(), instructions=PROMPT),
        )
        monitor_lab = MonitorLabAdapter(
            monitors=(EmptyLabMonitor(),),
            event_type=LabEvent,
        )
        monitors = (
            KeywordMonitor(),
            monitor_lab,
            local,
            frontier,
            investigator,
            ensemble,
        )
        for monitor in monitors:
            with self.subTest(monitor=monitor.name):
                result = evaluate_adversarial_monitor(
                    monitor,
                    self.clean_sets,
                    self.adversarial_sets,
                    bootstrap_iterations=0,
                )
                self.assertEqual(result["case_count"], 160)

    def test_provider_payloads_exclude_adversarial_labels(self) -> None:
        monitor = StructuredJudgeMonitor(provider=AllowProvider(), instructions=PROMPT)
        trace = as_contrast_sets(self.adversarial_sets)[0].variants[0]
        monitor.inspect(trace.for_monitor())
        payload = monitor.raw_records[0]["provider_payload"]
        encoded = json.dumps(payload)
        for hidden in (
            "adversarial_suite_version",
            "causal_policy_state_unchanged",
            "expected_control",
            "gold",
            "severity",
            "source_trace_id",
        ):
            self.assertNotIn(hidden, encoded)


@dataclass(frozen=True)
class _AllowMonitor:
    name: str = "test-allow"
    measure_latency: bool = False

    def inspect(self, trace: MonitorTrace):
        from control_bench.models import ControlAction, MonitorDecision

        return MonitorDecision.successful(
            trace_id=trace.trace_id,
            control=ControlAction.ALLOW,
            confidence=0.0,
            first_actionable_event=None,
            reason="Test policy allows the trace.",
        )
