from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol


class ControlAction(str, Enum):
    ALLOW = "allow"
    WARN = "warn"
    REVISE = "revise"
    REDACT = "redact"
    REQUEST_APPROVAL = "request_approval"
    SANDBOX = "sandbox"
    BLOCK = "block"


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

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "GoldDecision":
        return cls(
            label=str(payload["label"]),
            control=ControlAction(payload["control"]),
            first_actionable_event=payload.get("first_actionable_event"),
            evidence=tuple(EvidenceTarget.from_dict(item) for item in payload.get("evidence", [])),
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
    set_id: str
    title: str
    failure_mode: str
    policy_rule: str
    variants: tuple[TraceVariant, ...]
    comparisons: tuple[ContrastComparison, ...]

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ContrastSet":
        return cls(
            set_id=str(payload["set_id"]),
            title=str(payload["title"]),
            failure_mode=str(payload["failure_mode"]),
            policy_rule=str(payload["policy_rule"]),
            variants=tuple(TraceVariant.from_dict(item) for item in payload["variants"]),
            comparisons=tuple(ContrastComparison.from_dict(item) for item in payload["comparisons"]),
        )


@dataclass(frozen=True)
class MonitorDecision:
    trace_id: str
    control: ControlAction
    risk_score: float
    event_id: str | None
    evidence: tuple[EvidenceTarget, ...] = ()
    reason: str = ""
    latency_ms: float = 0.0
    token_cost: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "control": self.control.value,
            "risk_score": self.risk_score,
            "event_id": self.event_id,
            "evidence": [item.to_dict() for item in self.evidence],
            "reason": self.reason,
            "latency_ms": self.latency_ms,
            "token_cost": self.token_cost,
        }


class Monitor(Protocol):
    name: str

    def inspect(self, trace: TraceVariant) -> MonitorDecision:
        ...
