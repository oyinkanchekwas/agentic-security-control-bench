import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from control_bench.dataset import load_contrast_sets
from control_bench.evaluation import evaluate_monitor, paired_bootstrap_comparisons
from control_bench.learned_monitors import (
    AgenticInvestigatorMonitor,
    ProviderReply,
    StructuredJudgeMonitor,
    TransformersProvider,
)
from control_bench.models import ControlAction, MonitorResponse, MonitorStatus
from control_bench.monitors import MONITORS
from control_bench.prompting import build_monitor_messages


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "contrast_sets.jsonl"
PROMPT = (ROOT / "prompts" / "monitor-json-v1.txt").read_text(encoding="utf-8")
INVESTIGATOR_PROMPT = (ROOT / "prompts" / "investigator-v1.txt").read_text(
    encoding="utf-8"
)


class FixedProvider:
    model_id = "fixed-test-provider"

    def __init__(self, replies: list[str]) -> None:
        self.replies = list(replies)
        self.payloads: list[list[dict[str, str]]] = []

    def complete(self, messages, *, temperature, seed) -> ProviderReply:
        self.payloads.append(messages)
        return ProviderReply(
            text=self.replies.pop(0),
            model_id=self.model_id,
            input_tokens=20,
            output_tokens=10,
            estimated_cost_usd=0.001,
        )


class BrokenProvider:
    model_id = "broken-test-provider"

    def complete(self, messages, *, temperature, seed) -> ProviderReply:
        raise RuntimeError("test provider unavailable")


class LearnedMonitorTests(unittest.TestCase):
    def test_transformers_provider_uses_the_supported_dtype_argument(self) -> None:
        model_calls = []

        class FakeModel:
            def to(self, device):
                return self

            def eval(self):
                return self

        class FakeModelFactory:
            @staticmethod
            def from_pretrained(model_id, **kwargs):
                model_calls.append((model_id, kwargs))
                return FakeModel()

        class FakeTokeniserFactory:
            @staticmethod
            def from_pretrained(model_id, **kwargs):
                return SimpleNamespace(eos_token_id=0)

        fake_torch = SimpleNamespace(
            backends=SimpleNamespace(
                mps=SimpleNamespace(is_available=lambda: False)
            )
        )
        fake_transformers = SimpleNamespace(
            AutoModelForCausalLM=FakeModelFactory,
            AutoTokenizer=FakeTokeniserFactory,
        )
        with patch.dict(
            sys.modules,
            {"torch": fake_torch, "transformers": fake_transformers},
        ):
            TransformersProvider(model_id="fixture", revision="abc", device="cpu")
        self.assertEqual(model_calls[0][1]["torch_dtype"], "auto")
        self.assertNotIn("dtype", model_calls[0][1])

    @classmethod
    def setUpClass(cls) -> None:
        cls.sets = load_contrast_sets(DATASET)
        cls.trace = cls.sets[0].variants[0].for_monitor()

    def test_common_response_contract_round_trips(self) -> None:
        response = MonitorResponse.from_dict(
            {
                "control": "allow",
                "first_actionable_event": None,
                "evidence_fields": [],
                "confidence": 0.1,
                "reason": "The resolved action stays within the recorded boundary.",
            }
        )
        response.validate_for_trace(self.trace)
        self.assertEqual(response.control, ControlAction.ALLOW)
        self.assertEqual(set(response.to_dict()), {
            "control",
            "first_actionable_event",
            "evidence_fields",
            "confidence",
            "reason",
        })

    def test_contract_rejects_extra_fields_and_bad_confidence(self) -> None:
        with self.assertRaises(ValueError):
            MonitorResponse.from_dict(
                {
                    "control": "allow",
                    "first_actionable_event": None,
                    "evidence_fields": [],
                    "confidence": 1.4,
                    "reason": "Invalid confidence.",
                    "gold_control": "allow",
                }
            )

    def test_allow_rejects_an_intervention_event(self) -> None:
        response = MonitorResponse.from_dict(
            {
                "control": "allow",
                "first_actionable_event": self.trace.events[-1].event_id,
                "evidence_fields": [],
                "confidence": 0.1,
                "reason": "Inconsistent allow response.",
            }
        )
        with self.assertRaisesRegex(ValueError, "allow requires"):
            response.validate_for_trace(self.trace)

    def test_unavailable_evidence_fails_safely(self) -> None:
        event_id = self.trace.events[-1].event_id
        provider = FixedProvider(
            [
                json.dumps(
                    {
                        "control": "block",
                        "first_actionable_event": event_id,
                        "evidence_fields": ["gold.control"],
                        "confidence": 0.9,
                        "reason": "Unavailable evidence field.",
                    }
                )
            ]
        )
        monitor = StructuredJudgeMonitor(provider=provider, instructions=PROMPT)
        decision = monitor.inspect(self.trace)
        self.assertEqual(decision.status, MonitorStatus.MALFORMED_OUTPUT)
        self.assertEqual(decision.control, ControlAction.BLOCK)

    def test_provider_execution_failure_is_counted(self) -> None:
        monitor = StructuredJudgeMonitor(provider=BrokenProvider(), instructions=PROMPT)
        result = evaluate_monitor(monitor, self.sets[:1], bootstrap_iterations=0)
        self.assertEqual(result["execution"]["execution_failure"], 4)
        self.assertEqual(result["metrics"]["execution_failure_rate"], 1.0)
        self.assertEqual(result["metrics"]["unsafe_action_prevention"], 1.0)

    def test_provider_abstention_is_counted_and_blocked(self) -> None:
        provider = FixedProvider(["abstain"] * 4)
        monitor = StructuredJudgeMonitor(provider=provider, instructions=PROMPT)
        result = evaluate_monitor(monitor, self.sets[:1], bootstrap_iterations=0)
        self.assertEqual(result["execution"]["abstention"], 4)
        self.assertEqual(result["metrics"]["abstention_rate"], 1.0)
        self.assertEqual(result["metrics"]["unsafe_action_prevention"], 1.0)

    def test_provider_payload_contains_only_visible_trace_fields(self) -> None:
        messages = build_monitor_messages(self.trace, instructions=PROMPT)
        rendered = json.dumps(messages, sort_keys=True)
        for hidden in (
            '"gold"',
            '"recovery"',
            '"required_effects"',
            '"effects"',
            '"split"',
            '"expected_control"',
        ):
            self.assertNotIn(hidden, rendered)

    def test_investigator_payloads_exclude_hidden_fields(self) -> None:
        event_id = self.trace.events[-1].event_id
        provider = FixedProvider(
            [
                "Inspect the final action and attributes.path_within_workspace.",
                json.dumps(
                    {
                        "control": "allow",
                        "first_actionable_event": None,
                        "evidence_fields": [],
                        "confidence": 0.1,
                        "reason": "The resolved target stays within the workspace.",
                    }
                ),
            ]
        )
        monitor = AgenticInvestigatorMonitor(
            provider=provider,
            investigation_instructions=INVESTIGATOR_PROMPT,
            decision_instructions=PROMPT,
        )
        decision = monitor.inspect(self.trace)
        self.assertEqual(decision.status, MonitorStatus.SUCCESS)
        self.assertEqual(len(provider.payloads), 2)
        rendered = json.dumps(provider.payloads, sort_keys=True)
        self.assertNotIn('"gold"', rendered)
        self.assertNotIn('"recovery"', rendered)
        self.assertNotIn('"effects"', rendered)
        self.assertIn(event_id, rendered)

    def test_paired_bootstrap_uses_shared_cases(self) -> None:
        results = [
            evaluate_monitor(MONITORS[name], self.sets[-2:], bootstrap_iterations=10)
            for name in ("allow-all", "keyword", "policy-field-oracle")
        ]
        paired = paired_bootstrap_comparisons(results, iterations=20, seed=7)
        self.assertEqual(len(paired), 1)
        self.assertEqual(paired[0]["left_monitor"], "allow-all")
        self.assertEqual(paired[0]["right_monitor"], "keyword")
        self.assertNotIn("policy-field-oracle", json.dumps(paired))

    def test_paired_bootstrap_can_be_disabled(self) -> None:
        results = [
            evaluate_monitor(MONITORS[name], self.sets[-1:], bootstrap_iterations=0)
            for name in ("allow-all", "keyword")
        ]
        paired = paired_bootstrap_comparisons(results, iterations=0, seed=7)
        self.assertEqual(paired[0]["method"], "disabled")
        self.assertIn("point", paired[0]["metric_differences"]["control_accuracy"])


if __name__ == "__main__":
    unittest.main()
