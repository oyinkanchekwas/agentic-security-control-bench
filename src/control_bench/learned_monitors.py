from __future__ import annotations

from dataclasses import dataclass, field
import json
import os
from typing import Any, Protocol

from control_bench.models import (
    ControlAction,
    Monitor,
    MonitorDecision,
    MonitorResponse,
    MonitorStatus,
    MonitorTrace,
)
from control_bench.prompting import (
    build_investigator_decision_messages,
    build_investigator_messages,
    build_monitor_messages,
)


@dataclass(frozen=True)
class ProviderReply:
    text: str
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0


class TextProvider(Protocol):
    model_id: str

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        seed: int | None,
    ) -> ProviderReply:
        ...


@dataclass
class StructuredJudgeMonitor:
    provider: TextProvider
    instructions: str
    temperature: float = 0.0
    seed: int | None = None
    name: str = "structured-judge"
    raw_records: list[dict[str, Any]] = field(default_factory=list)

    def inspect(self, trace: MonitorTrace) -> MonitorDecision:
        messages = build_monitor_messages(trace, instructions=self.instructions)
        reply = self.provider.complete(messages, temperature=self.temperature, seed=self.seed)
        self.raw_records.append(
            {
                "trace_id": trace.trace_id,
                "provider_payload": {"messages": messages},
                "provider_response": reply.text,
                "model_id": reply.model_id,
            }
        )
        return _decision_from_reply(trace, reply)


@dataclass
class AgenticInvestigatorMonitor:
    provider: TextProvider
    investigation_instructions: str
    decision_instructions: str
    temperature: float = 0.0
    seed: int | None = None
    name: str = "agentic-investigator"
    raw_records: list[dict[str, Any]] = field(default_factory=list)

    def inspect(self, trace: MonitorTrace) -> MonitorDecision:
        first_messages = build_investigator_messages(
            trace, instructions=self.investigation_instructions
        )
        investigation = self.provider.complete(
            first_messages, temperature=self.temperature, seed=self.seed
        )
        second_messages = build_investigator_decision_messages(
            trace,
            instructions=self.decision_instructions,
            investigation=investigation.text,
        )
        decision_reply = self.provider.complete(
            second_messages, temperature=self.temperature, seed=self.seed
        )
        self.raw_records.append(
            {
                "trace_id": trace.trace_id,
                "provider_payloads": [
                    {"messages": first_messages},
                    {"messages": second_messages},
                ],
                "provider_responses": [investigation.text, decision_reply.text],
                "model_id": decision_reply.model_id,
            }
        )
        combined = ProviderReply(
            text=decision_reply.text,
            model_id=decision_reply.model_id,
            input_tokens=investigation.input_tokens + decision_reply.input_tokens,
            output_tokens=investigation.output_tokens + decision_reply.output_tokens,
            estimated_cost_usd=(
                investigation.estimated_cost_usd + decision_reply.estimated_cost_usd
            ),
        )
        return _decision_from_reply(trace, combined)


@dataclass
class DeterministicModelEnsemble:
    deterministic: Monitor
    learned: Monitor
    name: str = "deterministic-model-ensemble"

    def inspect(self, trace: MonitorTrace) -> MonitorDecision:
        fixed = self.deterministic.inspect(trace)
        learned = self.learned.inspect(trace)
        if learned.status is not MonitorStatus.SUCCESS:
            return learned
        if fixed.control is learned.control:
            selected = learned
            control = learned.control
        else:
            control = _combine_controls(fixed.control, learned.control)
            selected = max((fixed, learned), key=lambda item: item.response.confidence)
        event_id = selected.event_id
        if control is ControlAction.ALLOW:
            event_id = None
        reason = (
            f"Deterministic control {fixed.control.value}; model control "
            f"{learned.control.value}."
        )
        return MonitorDecision.successful(
            trace_id=trace.trace_id,
            control=control,
            confidence=(fixed.response.confidence + learned.response.confidence) / 2,
            first_actionable_event=event_id,
            evidence_fields=selected.response.evidence_fields if event_id else (),
            reason=reason,
            latency_ms=fixed.latency_ms + learned.latency_ms,
            input_tokens=learned.input_tokens,
            output_tokens=learned.output_tokens,
            estimated_cost_usd=learned.estimated_cost_usd,
        )


class TransformersProvider:
    def __init__(
        self,
        *,
        model_id: str,
        revision: str,
        max_new_tokens: int = 192,
        local_files_only: bool = False,
        device: str = "auto",
    ) -> None:
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "Install the local-model extra to run a local instruction model."
            ) from exc

        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self._torch = torch
        self._tokeniser = AutoTokenizer.from_pretrained(
            model_id,
            revision=revision,
            local_files_only=local_files_only,
        )
        self._model = AutoModelForCausalLM.from_pretrained(
            model_id,
            revision=revision,
            local_files_only=local_files_only,
            dtype="auto",
        )
        if device == "auto":
            device = "mps" if torch.backends.mps.is_available() else "cpu"
        self._device = device
        self._model.to(device)
        self._model.eval()

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        seed: int | None,
    ) -> ProviderReply:
        torch = self._torch
        if seed is not None:
            torch.manual_seed(seed)
        inputs = self._tokeniser.apply_chat_template(
            messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        )
        inputs = {key: value.to(self._device) for key, value in inputs.items()}
        generation_args: dict[str, Any] = {
            "max_new_tokens": self.max_new_tokens,
            "do_sample": temperature > 0,
            "pad_token_id": self._tokeniser.eos_token_id,
        }
        if temperature > 0:
            generation_args["temperature"] = temperature
        else:
            generation_args.update({"temperature": None, "top_p": None, "top_k": None})
        with torch.inference_mode():
            generated = self._model.generate(**inputs, **generation_args)
        input_length = inputs["input_ids"].shape[-1]
        output = generated[0, input_length:]
        text = self._tokeniser.decode(output, skip_special_tokens=True)
        return ProviderReply(
            text=text,
            model_id=self.model_id,
            input_tokens=int(input_length),
            output_tokens=int(output.shape[-1]),
        )


class ChatCompletionsProvider:
    def __init__(
        self,
        *,
        model_id: str,
        base_url: str,
        api_key_environment: str,
        timeout_seconds: float = 60.0,
        input_cost_per_million: float = 0.0,
        output_cost_per_million: float = 0.0,
    ) -> None:
        try:
            import httpx
        except ImportError as exc:
            raise RuntimeError(
                "Install the remote-model extra to run a remote judge."
            ) from exc
        self._httpx = httpx
        self.model_id = model_id
        self.base_url = base_url.rstrip("/")
        self.api_key_environment = api_key_environment
        self.timeout_seconds = timeout_seconds
        self.input_cost_per_million = input_cost_per_million
        self.output_cost_per_million = output_cost_per_million

    def complete(
        self,
        messages: list[dict[str, str]],
        *,
        temperature: float,
        seed: int | None,
    ) -> ProviderReply:
        api_key = os.environ.get(self.api_key_environment)
        if not api_key:
            raise RuntimeError(f"{self.api_key_environment} is not set")
        payload: dict[str, Any] = {
            "model": self.model_id,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
        }
        if seed is not None:
            payload["seed"] = seed
        response = self._httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        usage = body.get("usage", {})
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        cost = (
            input_tokens * self.input_cost_per_million
            + output_tokens * self.output_cost_per_million
        ) / 1_000_000
        return ProviderReply(
            text=str(body["choices"][0]["message"]["content"]),
            model_id=self.model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            estimated_cost_usd=cost,
        )


def _decision_from_reply(trace: MonitorTrace, reply: ProviderReply) -> MonitorDecision:
    if reply.text.strip().lower() in {"abstain", "abstention"}:
        return MonitorDecision.fail_safe(
            trace=trace,
            status=MonitorStatus.ABSTENTION,
            detail="provider abstained",
            input_tokens=reply.input_tokens,
            output_tokens=reply.output_tokens,
            estimated_cost_usd=reply.estimated_cost_usd,
        )
    try:
        payload = _parse_json_object(reply.text)
        response = MonitorResponse.from_dict(payload)
        response.validate_for_trace(trace)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        return MonitorDecision.fail_safe(
            trace=trace,
            status=MonitorStatus.MALFORMED_OUTPUT,
            detail=f"{type(exc).__name__}: invalid structured response",
            input_tokens=reply.input_tokens,
            output_tokens=reply.output_tokens,
            estimated_cost_usd=reply.estimated_cost_usd,
        )
    return MonitorDecision(
        trace_id=trace.trace_id,
        response=response,
        input_tokens=reply.input_tokens,
        output_tokens=reply.output_tokens,
        estimated_cost_usd=reply.estimated_cost_usd,
    )


def _parse_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[-1].strip() == "```":
            stripped = "\n".join(lines[1:-1]).strip()
            if stripped.startswith("json"):
                stripped = stripped[4:].lstrip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        raise ValueError("no JSON object found")
    payload = json.loads(stripped[start : end + 1])
    if not isinstance(payload, dict):
        raise ValueError("response is not a JSON object")
    return payload


def _combine_controls(left: ControlAction, right: ControlAction) -> ControlAction:
    if ControlAction.BLOCK in {left, right}:
        return ControlAction.REQUIRE_APPROVAL
    if ControlAction.REQUIRE_APPROVAL in {left, right}:
        return ControlAction.REQUIRE_APPROVAL
    if ControlAction.WARN in {left, right}:
        return ControlAction.WARN
    return ControlAction.ALLOW
