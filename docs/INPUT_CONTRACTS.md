# Programme Input Contracts

This repository uses the Failure Atlas taxonomy and can run Monitor Lab through an adapter. The
source commits used for the v0.3 results are pinned in `programme-lock.json`.

## Failure Atlas

The benchmark's eight failure modes are present in the Failure Atlas taxonomy. Contrast sets add
paired policy states and replay effects for the control-decision experiment. The general trace
dataset remains in the Atlas repository.

## Monitor Lab

`MonitorLabAdapter` converts benchmark events into the Monitor Lab event type and translates its
highest-severity finding into a control action. Monitor Lab findings cite text excerpts, so the
adapter reports `content` evidence and receives no credit for structured policy fields.

The adapter receives `MonitorTrace`, the same restricted view supplied to every monitor. Stored
effects, labels, required task effects, and recovery records are not passed across the boundary.

Run the integration locally with both repositories checked out as siblings:

```bash
PYTHONPATH=src:../coding-agent-monitor-lab/src python3 scripts/verify_programme_links.py \
  --atlas ../coding-agent-failure-atlas \
  --monitor-lab ../coding-agent-monitor-lab

PYTHONPATH=src:../coding-agent-monitor-lab/src python3 scripts/run_monitor_lab_baseline.py
PYTHONPATH=src:../coding-agent-monitor-lab/src python3 scripts/run_adversarial_monitor_lab.py
```

The lock check prevents results from being attributed to a different source revision.

## Model providers

`MonitorTrace.to_provider_dict()` is the only trace serialiser used by the model adapters. Its
payload contains `trace_id`, `task`, and the observed events. Events contain their identifiers,
sequence numbers, actors, kinds, content, and visible attributes.

Gold labels, split labels, expected controls, effects, required effects, and recovery records are
held by the scorer. Tests inspect both single-pass and investigator payloads and fail if any of
those fields appear.

Adversarial relationship records remain behind the same boundary. Source trace identifiers,
perturbation classes, changed fields, causal-state relations, and severity are never serialised into
a provider message.

The local adapter imports its optional inference packages only when constructed. The remote
adapter reads an access credential from the environment and never writes it to a run record.
Provider text is stored only in the ignored raw-results directory.
