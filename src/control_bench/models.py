from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from typing import Any, Protocol


class ControlAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    REQUIRE_APPROVAL = "require_approval"
    BLOCK = "block"


class MonitorStatus(str, Enum):
    SUCCESS = "success"
    ABSTENTION = "abstention"
    MALFORMED_OUTPUT = "malformed_output"
    EXECUTION_FAILURE = "execution_failure"


@dataclass(frozen=True)
class EvidenceTarget:
    event_id: str
    field: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EvidenceTarget":
        return cls(event_id=str(payload["event_id"]), field=str(payload["field"]))

    def to_dict(self) -> dict[str, str]:
        return {"event_id": self.event_id, "field": self.field}


@dataclass(frozen=True)
class Effect:
    effect_id: str
    status: str
    contributes_to_task: bool

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Effect":
        return cls(
            effect_id=str(payload["effect_id"]),
            status=str(payload["status"]),
            contributes_to_task=bool(payload.get("contributes_to_task", False)),
        )


@dataclass(frozen=True)
class TraceEvent:
    event_id: str
    sequence: int
    actor: str
    kind: str
    content: str
    attributes: dict[str, Any] = field(default_factory=dict)
    effects: tuple[Effect, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TraceEvent":
        return cls(
            event_id=str(payload["event_id"]),
            sequence=int(payload["sequence"]),
            actor=str(payload["actor"]),
            kind=str(payload["kind"]),
            content=str(payload["content"]),
            attributes=dict(payload.get("attributes", {})),
            effects=tuple(Effect.from_dict(item) for item in payload.get("effects", [])),
        )


@dataclass(frozen=True)
class ObservedEvent:
    event_id: str
    sequence: int
    actor: str
    kind: str
    content: str
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_provider_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "sequence": self.sequence,
            "actor": self.actor,
            "kind": self.kind,
            "content": self.content,
            "attributes": dict(self.attributes),
        }


@dataclass(frozen=True)
class MonitorTrace:
    trace_id: str
    task: str
    events: tuple[ObservedEvent, ...]

    def to_provider_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "task": self.task,
            "events": [event.to_provider_dict() for event in self.events],
        }

    def event(self, event_id: str) -> ObservedEvent | None:
        return next((event for event in self.events if event.event_id == event_id), None)


@dataclass(frozen=True)
class Recovery:
    accepted_controls: tuple[ControlAction, ...]
    events: tuple[TraceEvent, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Recovery":
        return cls(
            accepted_controls=tuple(ControlAction(item) for item in payload.get("accepted_controls", [])),
            events=tuple(TraceEvent.from_dict(item) for item in payload.get("events", [])),
        )


@dataclass(frozen=True)
class GoldDecision:
    label: str
    control: ControlAction
    first_actionable_event: str | None
    evidence: tuple[EvidenceTarget, ...]
    severity: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GoldDecision":
        return cls(
            label=str(payload["label"]),
            control=ControlAction(payload["control"]),
            first_actionable_event=payload.get("first_actionable_event"),
            evidence=tuple(EvidenceTarget.from_dict(item) for item in payload.get("evidence", [])),
            severity=str(payload.get("severity", "none")),
        )


@dataclass(frozen=True)
class TraceVariant:
    trace_id: str
    variant: str
    task: str
    events: tuple[TraceEvent, ...]
    required_effects: frozenset[str]
    gold: GoldDecision
    recovery: Recovery

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TraceVariant":
        return cls(
            trace_id=str(payload["trace_id"]),
            variant=str(payload["variant"]),
            task=str(payload["task"]),
            events=tuple(TraceEvent.from_dict(item) for item in payload["events"]),
            required_effects=frozenset(str(item) for item in payload.get("required_effects", [])),
            gold=GoldDecision.from_dict(payload["gold"]),
            recovery=Recovery.from_dict(payload.get("recovery", {})),
        )

    def for_monitor(self) -> MonitorTrace:
        return MonitorTrace(
            trace_id=self.trace_id,
            task=self.task,
            events=tuple(
                ObservedEvent(
                    event_id=event.event_id,
                    sequence=event.sequence,
                    actor=event.actor,
                    kind=event.kind,
                    content=event.content,
                    attributes=dict(event.attributes),
                )
                for event in self.events
            ),
        )


@dataclass(frozen=True)
class ContrastComparison:
    left: str
    right: str
    expected_relation: str
    changed_fields: tuple[str, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ContrastComparison":
        return cls(
            left=str(payload["left"]),
            right=str(payload["right"]),
            expected_relation=str(payload["expected_relation"]),
            changed_fields=tuple(str(item) for item in payload.get("changed_fields", [])),
        )


@dataclass(frozen=True)
class ContrastSet:
    benchmark_version: str
    set_id: str
    title: str
    failure_mode: str
    policy_rule: str
    split: str
    scenario_id: str
    template_id: str
    variants: tuple[TraceVariant, ...]
    comparisons: tuple[ContrastComparison, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ContrastSet":
        return cls(
            benchmark_version=str(payload["benchmark_version"]),
            set_id=str(payload["set_id"]),
            title=str(payload["title"]),
            failure_mode=str(payload["failure_mode"]),
            policy_rule=str(payload["policy_rule"]),
            split=str(payload["split"]),
            scenario_id=str(payload["scenario_id"]),
            template_id=str(payload["template_id"]),
            variants=tuple(TraceVariant.from_dict(item) for item in payload["variants"]),
            comparisons=tuple(ContrastComparison.from_dict(item) for item in payload["comparisons"]),
        )


@dataclass(frozen=True)
class MonitorResponse:
    control: ControlAction
    first_actionable_event: str | None
    evidence_fields: tuple[str, ...]
    confidence: float
    reason: str

    def __post_init__(self) -> None:
        if not isfinite(self.confidence) or not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be a finite number between 0 and 1")
        if not self.reason.strip():
            raise ValueError("reason must contain text")
        if len(self.reason) > 500:
            raise ValueError("reason must not exceed 500 characters")
        if len(set(self.evidence_fields)) != len(self.evidence_fields):
            raise ValueError("evidence_fields must not contain duplicates")
        if self.first_actionable_event is None and self.evidence_fields:
            raise ValueError("evidence_fields require first_actionable_event")

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MonitorResponse":
        required = {
            "control",
            "first_actionable_event",
            "evidence_fields",
            "confidence",
            "reason",
        }
        if set(payload) != required:
            missing = sorted(required - set(payload))
            extra = sorted(set(payload) - required)
            raise ValueError(f"response fields differ: missing={missing}, extra={extra}")
        evidence_fields = payload["evidence_fields"]
        if not isinstance(evidence_fields, list) or not all(
            isinstance(item, str) for item in evidence_fields
        ):
            raise ValueError("evidence_fields must be an array of strings")
        event_id = payload["first_actionable_event"]
        if event_id is not None and not isinstance(event_id, str):
            raise ValueError("first_actionable_event must be a string or null")
        confidence = payload["confidence"]
        if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
            raise ValueError("confidence must be numeric")
        reason = payload["reason"]
        if not isinstance(reason, str):
            raise ValueError("reason must be a string")
        return cls(
            control=ControlAction(payload["control"]),
            first_actionable_event=event_id,
            evidence_fields=tuple(evidence_fields),
            confidence=float(confidence),
            reason=reason,
        )

    def validate_for_trace(self, trace: MonitorTrace) -> None:
        if self.first_actionable_event is None:
            if self.control is not ControlAction.ALLOW:
                raise ValueError("an intervention control requires first_actionable_event")
            return
        if self.control is ControlAction.ALLOW:
            raise ValueError("allow requires a null first_actionable_event")
        event = trace.event(self.first_actionable_event)
        if event is None:
            raise ValueError("first_actionable_event is not present in the monitor trace")
        available = _event_field_paths(event)
        missing = sorted(set(self.evidence_fields) - available)
        if missing:
            raise ValueError(f"evidence fields are unavailable: {missing}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "control": self.control.value,
            "first_actionable_event": self.first_actionable_event,
            "evidence_fields": list(self.evidence_fields),
            "confidence": self.confidence,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class MonitorDecision:
    trace_id: str
    response: MonitorResponse
    status: MonitorStatus = MonitorStatus.SUCCESS
    failure_detail: str | None = None
    latency_ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    @property
    def control(self) -> ControlAction:
        return self.response.control

    @property
    def event_id(self) -> str | None:
        return self.response.first_actionable_event

    @property
    def evidence(self) -> tuple[EvidenceTarget, ...]:
        if self.event_id is None:
            return ()
        return tuple(EvidenceTarget(self.event_id, field) for field in self.response.evidence_fields)

    @classmethod
    def successful(
        cls,
        *,
        trace_id: str,
        control: ControlAction,
        confidence: float,
        first_actionable_event: str | None,
        evidence_fields: tuple[str, ...] = (),
        reason: str,
        latency_ms: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> "MonitorDecision":
        return cls(
            trace_id=trace_id,
            response=MonitorResponse(
                control=control,
                first_actionable_event=first_actionable_event,
                evidence_fields=evidence_fields,
                confidence=confidence,
                reason=reason,
            ),
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )

    @classmethod
    def fail_safe(
        cls,
        *,
        trace: MonitorTrace,
        status: MonitorStatus,
        detail: str,
        latency_ms: float = 0.0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost_usd: float = 0.0,
    ) -> "MonitorDecision":
        event = next(
            (item for item in trace.events if item.kind in {"action", "response"}),
            trace.events[-1],
        )
        return cls(
            trace_id=trace.trace_id,
            response=MonitorResponse(
                control=ControlAction.BLOCK,
                first_actionable_event=event.event_id,
                evidence_fields=(),
                confidence=1.0,
                reason="Monitor result unavailable; the action is blocked for review.",
            ),
            status=status,
            failure_detail=detail[:500],
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=estimated_cost_usd,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "response": self.response.to_dict(),
            "execution": {
                "status": self.status.value,
                "failure_detail": self.failure_detail,
                "latency_ms": self.latency_ms,
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "estimated_cost_usd": self.estimated_cost_usd,
            },
        }


class Monitor(Protocol):
    name: str

    def inspect(self, trace: MonitorTrace) -> MonitorDecision:
        ...


def _event_field_paths(event: ObservedEvent) -> set[str]:
    paths = {"event_id", "sequence", "actor", "kind", "content"}
    paths.update(f"attributes.{key}" for key in event.attributes)
    return paths
