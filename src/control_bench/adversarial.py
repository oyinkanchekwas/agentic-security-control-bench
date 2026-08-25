from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Iterable

from control_bench.dataset import validate_contrast_sets
from control_bench.models import ContrastSet, TraceVariant


SUITE_VERSION = "0.4.0"
BENCHMARK_VERSION = "0.4.0-adversarial"
FROZEN_CLEAN_SHA256 = "4e671d79e4698e50ee87407c7f3c6a2682610d47994d152856c2e4f1973eb443"
PERTURBATION_CLASSES = {
    "lexical_decoy",
    "policy_obscuring_paraphrase",
    "embedded_instruction_attack",
    "multi_event_composition",
    "deceptive_completion_verification",
}


@dataclass(frozen=True)
class AdversarialRelationship:
    source_trace_id: str
    source_scenario_id: str
    perturbation_class: str
    changed_fields: tuple[str, ...]
    causal_policy_state_unchanged: bool
    expected_control: str
    first_actionable_event: str | None
    causal_evidence_fields: tuple[str, ...]
    severity: str
    status: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AdversarialRelationship":
        changed_fields = payload["changed_fields"]
        evidence_fields = payload["causal_evidence_fields"]
        state_unchanged = payload["causal_policy_state_unchanged"]
        first_actionable_event = payload.get("first_actionable_event")
        if not isinstance(changed_fields, list) or not all(
            isinstance(item, str) for item in changed_fields
        ):
            raise ValueError("changed_fields must be an array of strings")
        if not isinstance(evidence_fields, list) or not all(
            isinstance(item, str) for item in evidence_fields
        ):
            raise ValueError("causal_evidence_fields must be an array of strings")
        if not isinstance(state_unchanged, bool):
            raise ValueError("causal_policy_state_unchanged must be boolean")
        if first_actionable_event is not None and not isinstance(first_actionable_event, str):
            raise ValueError("first_actionable_event must be a string or null")
        return cls(
            source_trace_id=str(payload["source_trace_id"]),
            source_scenario_id=str(payload["source_scenario_id"]),
            perturbation_class=str(payload["perturbation_class"]),
            changed_fields=tuple(changed_fields),
            causal_policy_state_unchanged=state_unchanged,
            expected_control=str(payload["expected_control"]),
            first_actionable_event=first_actionable_event,
            causal_evidence_fields=tuple(evidence_fields),
            severity=str(payload["severity"]),
            status=str(payload["status"]),
        )


@dataclass(frozen=True)
class AdversarialTrace:
    trace: TraceVariant
    relationship: AdversarialRelationship


@dataclass(frozen=True)
class AdversarialSet:
    suite_version: str
    content_safety: str
    perturbation_class: str
    contrast_set: ContrastSet
    traces: tuple[AdversarialTrace, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "AdversarialSet":
        contrast_set = ContrastSet.from_dict(payload)
        traces = tuple(
            AdversarialTrace(
                trace=trace,
                relationship=AdversarialRelationship.from_dict(raw["adversarial"]),
            )
            for trace, raw in zip(contrast_set.variants, payload["variants"], strict=True)
        )
        return cls(
            suite_version=str(payload["adversarial_suite_version"]),
            content_safety=str(payload["content_safety"]),
            perturbation_class=str(payload["perturbation_class"]),
            contrast_set=contrast_set,
            traces=traces,
        )


def load_adversarial_sets(path: str | Path) -> tuple[AdversarialSet, ...]:
    source = Path(path)
    records: list[AdversarialSet] = []
    with source.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                records.append(AdversarialSet.from_dict(payload))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{source}:{line_number}: {exc}") from exc
    return tuple(records)


def clean_dataset_digest(path: str | Path) -> str:
    return sha256(Path(path).read_bytes()).hexdigest()


def validate_adversarial_sets(
    adversarial_sets: Iterable[AdversarialSet],
    clean_sets: Iterable[ContrastSet],
    *,
    clean_digest: str,
) -> list[str]:
    sets = tuple(adversarial_sets)
    clean = tuple(clean_sets)
    errors = validate_contrast_sets(
        as_contrast_sets(sets),
        valid_splits={"adversarial_holdout"},
        require_unique_template_ids=False,
    )
    if clean_digest != FROZEN_CLEAN_SHA256:
        errors.append("the frozen v0.3 dataset digest has changed")

    clean_index = {
        trace.trace_id: (contrast_set, trace)
        for contrast_set in clean
        for trace in contrast_set.variants
    }
    set_ids: set[str] = set()
    trace_ids: set[str] = set()
    source_ids: set[str] = set()
    family_sets: Counter[str] = Counter()
    family_traces: Counter[str] = Counter()
    class_sets: Counter[str] = Counter()
    class_traces: Counter[str] = Counter()
    family_status: Counter[tuple[str, str]] = Counter()
    class_status: Counter[tuple[str, str]] = Counter()

    for item in sets:
        contrast_set = item.contrast_set
        set_sources = {trace.relationship.source_trace_id for trace in item.traces}
        unchanged_count = sum(
            trace.relationship.causal_policy_state_unchanged for trace in item.traces
        )
        if len(set_sources) != 1:
            errors.append(f"{contrast_set.set_id}: traces do not share one clean counterpart")
        if unchanged_count != 2:
            errors.append(f"{contrast_set.set_id}: expected two policy-preserving traces")
        if item.suite_version != SUITE_VERSION:
            errors.append(f"{contrast_set.set_id}: suite version must be {SUITE_VERSION}")
        if contrast_set.benchmark_version != BENCHMARK_VERSION:
            errors.append(
                f"{contrast_set.set_id}: benchmark version must be {BENCHMARK_VERSION}"
            )
        if contrast_set.split != "adversarial_holdout":
            errors.append(f"{contrast_set.set_id}: split must be adversarial_holdout")
        if item.content_safety != "synthetic_inert":
            errors.append(f"{contrast_set.set_id}: content_safety must be synthetic_inert")
        if item.perturbation_class not in PERTURBATION_CLASSES:
            errors.append(f"{contrast_set.set_id}: unknown perturbation class")
        if contrast_set.set_id in set_ids:
            errors.append(f"duplicate set id: {contrast_set.set_id}")
        set_ids.add(contrast_set.set_id)
        family_sets[contrast_set.failure_mode] += 1
        class_sets[item.perturbation_class] += 1
        if len(item.traces) != 4:
            errors.append(f"{contrast_set.set_id}: expected four adversarial traces")

        for adversarial_trace in item.traces:
            trace = adversarial_trace.trace
            relation = adversarial_trace.relationship
            if trace.trace_id in trace_ids:
                errors.append(f"duplicate trace id: {trace.trace_id}")
            trace_ids.add(trace.trace_id)
            source_ids.add(relation.source_trace_id)
            family_traces[contrast_set.failure_mode] += 1
            class_traces[item.perturbation_class] += 1
            family_status[(contrast_set.failure_mode, trace.gold.label)] += 1
            class_status[(item.perturbation_class, trace.gold.label)] += 1

            source_record = clean_index.get(relation.source_trace_id)
            if source_record is None:
                errors.append(f"{trace.trace_id}: clean counterpart was not found")
                continue
            source_set, source_trace = source_record
            if source_set.split != "test":
                errors.append(f"{trace.trace_id}: clean counterpart is not in the v0.3 test split")
            if source_set.scenario_id != relation.source_scenario_id:
                errors.append(f"{trace.trace_id}: source scenario does not match")
            if source_set.failure_mode != contrast_set.failure_mode:
                errors.append(f"{trace.trace_id}: source policy family does not match")
            if relation.perturbation_class != item.perturbation_class:
                errors.append(f"{trace.trace_id}: perturbation class does not match its set")
            if not relation.changed_fields:
                errors.append(f"{trace.trace_id}: changed_fields is empty")

            unchanged = trace.gold.label == source_trace.gold.label
            if unchanged != relation.causal_policy_state_unchanged:
                errors.append(f"{trace.trace_id}: causal policy-state relation is wrong")
            if relation.expected_control != trace.gold.control.value:
                errors.append(f"{trace.trace_id}: expected control does not match gold")
            if relation.first_actionable_event != trace.gold.first_actionable_event:
                errors.append(f"{trace.trace_id}: first actionable event does not match gold")
            evidence_fields = tuple(target.field for target in trace.gold.evidence)
            if relation.causal_evidence_fields != evidence_fields:
                errors.append(f"{trace.trace_id}: causal evidence fields do not match gold")
            if relation.severity != trace.gold.severity:
                errors.append(f"{trace.trace_id}: severity does not match gold")
            if relation.status != trace.gold.label:
                errors.append(f"{trace.trace_id}: status does not match gold")
            if not unchanged and trace.gold.control is source_trace.gold.control:
                errors.append(f"{trace.trace_id}: changed policy state kept the source control")

    if len(sets) != 40:
        errors.append(f"expected 40 adversarial sets, found {len(sets)}")
    if len(trace_ids) != 160:
        errors.append(f"expected 160 adversarial traces, found {len(trace_ids)}")
    if len(source_ids) != 40:
        errors.append(f"expected 40 clean counterparts, found {len(source_ids)}")
    if set(class_sets) != PERTURBATION_CLASSES:
        errors.append("perturbation-class coverage is incomplete")
    for perturbation_class in PERTURBATION_CLASSES:
        if class_sets[perturbation_class] != 8:
            errors.append(f"{perturbation_class}: expected eight sets")
        if class_traces[perturbation_class] != 32:
            errors.append(f"{perturbation_class}: expected 32 traces")
        for status in ("permitted", "unsafe"):
            if class_status[(perturbation_class, status)] != 16:
                errors.append(f"{perturbation_class}: expected 16 {status} traces")
    families = {item.failure_mode for item in clean}
    for family in families:
        if family_sets[family] != 5:
            errors.append(f"{family}: expected five adversarial sets")
        if family_traces[family] != 20:
            errors.append(f"{family}: expected 20 adversarial traces")
        for status in ("permitted", "unsafe"):
            if family_status[(family, status)] != 10:
                errors.append(f"{family}: expected ten {status} traces")
    return errors


def as_contrast_sets(adversarial_sets: Iterable[AdversarialSet]) -> tuple[ContrastSet, ...]:
    return tuple(item.contrast_set for item in adversarial_sets)


def relationships_by_trace(
    adversarial_sets: Iterable[AdversarialSet],
) -> dict[str, AdversarialRelationship]:
    return {
        item.trace.trace_id: item.relationship
        for adversarial_set in adversarial_sets
        for item in adversarial_set.traces
    }
