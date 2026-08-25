# Prior Work and Experimental Scope

This targeted review was last checked on 25 August 2026. It covers benchmark and control work
closest to the experiment in this repository. It is not a systematic review.

| Project | Evaluated problem | Boundary used here |
| --- | --- | --- |
| [AgentDojo](https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html) | Prompt-injection attacks and defences for tool-using agents, with security and utility measures | This repository concentrates on coding traces, structured evidence fields, and control selection |
| [Agent Security Bench](https://openreview.net/pdf?id=V4y0CpX4hK) | Attacks and defences across ten agent settings and over 400 tools | The present dataset uses small counterfactual trace sets with executable effect checks |
| [ControlArena](https://control-arena.aisi.org.uk/monitors.html) | Step-level suspicion scoring and control protocols | This evaluator requires an event citation, field citations, and one discrete control |
| [MonitoringBench](https://arxiv.org/abs/2605.09684) | Semi-automated red-teaming of coding-agent monitors on 2,644 attack trajectories | The present experiment tests evidence attribution under controlled trace edits |
| [SLEIGHT-Bench](https://arxiv.org/abs/2605.16626) | Evasion attacks against coding-agent monitors | The cases are paired with permitted lexical decoys and low-signal unsafe traces |
| [StepShield](https://github.com/glo26/stepshield) | A public 2026 repository centred on intervention timing | Timing is recorded here, but causal field evidence and control choice form the main task |
| [OSGuard](https://arxiv.org/abs/2606.15034) | Contextual action safety and state-based invariants for computer-use agents | This work applies contrastive state checks to coding-agent traces and evaluates cited evidence fields |
| [PASTABench](https://openreview.net/pdf?id=2IqSjWFIxd) | Proactive monitoring with temporal and categorical ground truth | The present metric asks whether the selected evidence changes under the labelled counterfactual |
| [Execution-Grounded Security Testing](https://arxiv.org/abs/2607.22569) | Coding-agent security tests verified through tool traces and file-system changes | The replay engine uses declared effects and performs no live unsafe operations |
| [AgentTelemetry](https://openreview.net/pdf?id=owdmAYFk6k) | Fault detection, typed spans, and intervention for agent observability | This benchmark scores policy-field evidence and counterfactual decision behaviour |
| [Counterfactual attribution evaluation](https://arxiv.org/abs/2408.11252) | Counterfactual tests for attribution faithfulness in autoregressive models | The same evaluation principle is applied to monitor citations over structured coding-agent events |

The reviewed coding-agent benchmarks cover attack success, monitor catch rate, timing, task utility,
and execution evidence. I found no coding-agent benchmark in this set that jointly scores a discrete
control decision, exact event-and-field citations, counterfactual decision sensitivity, citation
stability, and task-preserving replay.

That finding is bounded by the sources above and the review date. The repository describes the
experiment directly and makes no priority claim.
