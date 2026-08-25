from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from control_bench.models import ContrastSet, ControlAction, TraceVariant
from control_bench.replay import replay_trace


VALID_LABELS = {"permitted", "unsafe"}
VALID_RELATIONS = {"same", "flip"}


def load_contrast_sets(path: str | Path) -> tuple[ContrastSet, ...]:
    source = Path(path)
    records: list[dict[str, Any]] = []
    with source.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{source}:{line_number}: invalid JSON: {exc}") from exc
    return tuple(ContrastSet.from_dict(record) for record in records)


def validate_contrast_sets(contrast_sets: Iterable[ContrastSet]) -> list[str]:
    errors: list[str] = []
    set_ids: set[str] = set()
    trace_ids: set[str] = set()
    for contrast_set in contrast_sets:
        if contrast_set.set_id in set_ids:
            errors.append(f"{contrast_set.set_id}: duplicate set id")
        set_ids.add(contrast_set.set_id)

        if len(contrast_set.variants) != 4:
            errors.append(f"{contrast_set.set_id}: expected four variants")

        labels = [variant.gold.label for variant in contrast_set.variants]
        if labels.count("permitted") != 2 or labels.count("unsafe") != 2:
            errors.append(f"{contrast_set.set_id}: expected two permitted and two unsafe variants")

        variants_by_name = {variant.variant: variant for variant in contrast_set.variants}
        if len(variants_by_name) != len(contrast_set.variants):
            errors.append(f"{contrast_set.set_id}: duplicate variant name")

        for variant in contrast_set.variants:
            errors.extend(_validate_variant(variant, trace_ids))
            trace_ids.add(variant.trace_id)

        for comparison in contrast_set.comparisons:
            if comparison.left not in variants_by_name or comparison.right not in variants_by_name:
                errors.append(f"{contrast_set.set_id}: comparison references an unknown variant")
                continue
            if comparison.expected_relation not in VALID_RELATIONS:
                errors.append(f"{contrast_set.set_id}: invalid relation {comparison.expected_relation!r}")
            left_label = variants_by_name[comparison.left].gold.label
            right_label = variants_by_name[comparison.right].gold.label
            observed = "same" if left_label == right_label else "flip"
            if observed != comparison.expected_relation:
                errors.append(
                    f"{contrast_set.set_id}: comparison label relation is {observed}, "
                    f"expected {comparison.expected_relation}"
                )
            if not comparison.changed_fields:
                errors.append(f"{contrast_set.set_id}: comparison has no changed fields")
    return errors


def _validate_variant(variant: TraceVariant, trace_ids: set[str]) -> list[str]:
    errors: list[str] = []
    if variant.trace_id in trace_ids:
        errors.append(f"{variant.trace_id}: duplicate trace id")
    if variant.gold.label not in VALID_LABELS:
        errors.append(f"{variant.trace_id}: invalid label {variant.gold.label!r}")
    if not variant.events:
        errors.append(f"{variant.trace_id}: trace has no events")
        return errors

    sequences = [event.sequence for event in variant.events]
    if sequences != sorted(sequences) or len(sequences) != len(set(sequences)):
        errors.append(f"{variant.trace_id}: event sequence must be ordered and unique")
    event_ids = {event.event_id for event in variant.events}
    if len(event_ids) != len(variant.events):
        errors.append(f"{variant.trace_id}: duplicate event id")

    if variant.gold.label == "permitted":
        if variant.gold.control is not ControlAction.ALLOW:
            errors.append(f"{variant.trace_id}: permitted trace must use allow")
        if variant.gold.first_actionable_event is not None:
            errors.append(f"{variant.trace_id}: permitted trace has an intervention point")
    else:
        if variant.gold.control is ControlAction.ALLOW:
            errors.append(f"{variant.trace_id}: unsafe trace uses allow")
        if variant.gold.first_actionable_event not in event_ids:
            errors.append(f"{variant.trace_id}: intervention point is missing from the trace")
        if not variant.gold.evidence:
            errors.append(f"{variant.trace_id}: unsafe trace has no evidence target")

    events_by_id = {event.event_id: event for event in variant.events}
    for evidence in variant.gold.evidence:
        event = events_by_id.get(evidence.event_id)
        if event is None:
            errors.append(f"{variant.trace_id}: evidence references an unknown event")
            continue
        if evidence.field.startswith("attributes."):
            key = evidence.field.removeprefix("attributes.")
            if key not in event.attributes:
                errors.append(f"{variant.trace_id}: evidence field {evidence.field!r} is absent")

    allow_outcome = replay_trace(variant, ControlAction.ALLOW)
    gold_outcome = replay_trace(variant, variant.gold.control)
    if variant.gold.label == "permitted" and (allow_outcome.harm or not allow_outcome.task_complete):
        errors.append(f"{variant.trace_id}: permitted trace does not complete safely under allow")
    if variant.gold.label == "unsafe" and not allow_outcome.harm:
        errors.append(f"{variant.trace_id}: unsafe trace has no prohibited effect under allow")
    if gold_outcome.harm or not gold_outcome.task_complete:
        errors.append(f"{variant.trace_id}: gold control does not produce a safe completion")
    return errors
