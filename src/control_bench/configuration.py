from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from control_bench.learned_monitors import (
    AgenticInvestigatorMonitor,
    ChatCompletionsProvider,
    DeterministicModelEnsemble,
    StructuredJudgeMonitor,
    TransformersProvider,
)
from control_bench.monitors import MONITORS


def load_run_config(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {"name", "monitor_kind", "provider", "split", "prompt_version"}
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"monitor configuration is missing fields: {missing}")
    if payload["split"] not in {"train", "dev", "test"}:
        raise ValueError("learned monitor runs require one named dataset split")
    return payload


def build_configured_monitor(config: dict[str, Any], root: Path):
    provider = _build_provider(config["provider"])
    temperature = float(config.get("temperature", 0.0))
    seed = config.get("seed")
    if seed is not None:
        seed = int(seed)
    monitor_kind = config["monitor_kind"]
    if monitor_kind == "structured_judge":
        monitor = StructuredJudgeMonitor(
            provider=provider,
            instructions=_read_prompt(root, config["prompt_path"]),
            temperature=temperature,
            seed=seed,
            name=str(config["name"]),
        )
    elif monitor_kind == "agentic_investigator":
        monitor = AgenticInvestigatorMonitor(
            provider=provider,
            investigation_instructions=_read_prompt(
                root, config["investigation_prompt_path"]
            ),
            decision_instructions=_read_prompt(root, config["prompt_path"]),
            temperature=temperature,
            seed=seed,
            name=str(config["name"]),
        )
    elif monitor_kind == "ensemble":
        learned = StructuredJudgeMonitor(
            provider=provider,
            instructions=_read_prompt(root, config["prompt_path"]),
            temperature=temperature,
            seed=seed,
            name=f"{config['name']}-model",
        )
        base_name = str(config["deterministic_monitor"])
        if base_name not in MONITORS or base_name == "policy-field-oracle":
            raise ValueError("ensemble requires a deployable deterministic monitor")
        monitor = DeterministicModelEnsemble(
            deterministic=MONITORS[base_name],
            learned=learned,
            name=str(config["name"]),
        )
    else:
        raise ValueError(f"unknown monitor_kind: {monitor_kind}")
    return monitor


def prompt_paths(config: dict[str, Any], root: Path) -> tuple[Path, ...]:
    keys = ("prompt_path", "investigation_prompt_path")
    return tuple(root / config[key] for key in keys if key in config)


def _build_provider(config: dict[str, Any]):
    provider_kind = config["kind"]
    if provider_kind == "transformers":
        return TransformersProvider(
            model_id=str(config["model_id"]),
            revision=str(config["revision"]),
            max_new_tokens=int(config.get("max_new_tokens", 192)),
            local_files_only=bool(config.get("local_files_only", False)),
            device=str(config.get("device", "auto")),
        )
    if provider_kind == "chat_completions":
        return ChatCompletionsProvider(
            model_id=str(config["model_id"]),
            base_url=str(config["base_url"]),
            api_key_environment=str(config["api_key_environment"]),
            timeout_seconds=float(config.get("timeout_seconds", 60.0)),
            input_cost_per_million=float(config.get("input_cost_per_million", 0.0)),
            output_cost_per_million=float(config.get("output_cost_per_million", 0.0)),
        )
    raise ValueError(f"unknown provider kind: {provider_kind}")


def _read_prompt(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")
