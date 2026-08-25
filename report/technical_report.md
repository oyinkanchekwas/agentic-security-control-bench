# Evidence-Grounded Control Decisions for Coding-Agent Traces

Oyinkansola Onwuchekwa

Version 0.2 report, 25 August 2026

## Abstract

Coding-agent monitors often return a risk score and prose explanation. Those outputs leave two
operational questions unresolved: which trace fields support the decision, and which control can
prevent harm while preserving the task? This report presents a contrastive benchmark that requires
event-and-field evidence, a discrete control action, and a replay check. Version 0.2 contains 256
synthetic traces across eight policy families, with disjoint semantic scenarios for train,
development, and test.

## 1. Problem

A monitor can produce the correct unsafe label for the wrong reason. Keyword matching may flag a
permitted security fixture because it contains terms associated with secrets or deletion. The same
monitor may miss an unsafe action written in ordinary operational language.

The benchmark tests decisions across controlled trace edits. A policy-bearing field changes
between permitted and unsafe variants, while decoy variants alter wording without changing the
policy state. The monitor identifies the first actionable event and cites the precise fields behind
its control.

## 2. Relation to existing evaluations

AgentDojo evaluates security and utility under prompt injection. ControlArena supports online
monitoring and control protocols. MonitoringBench and SLEIGHT-Bench examine attacks that evade
coding-agent monitors. StepShield and PASTABench study intervention timing, while OSGuard combines
contextual action labels with state-based safety checks.

This experiment concentrates on causal evidence at trace-field level and replayed task effects.
The prior-work table in `docs/PRIOR_WORK.md` records the review boundary and access date.

## 3. Dataset

The dataset covers eight policy families:

1. filesystem workspace scope;
2. approved outbound destinations;
3. publication approval;
4. dependency source and revision checks;
5. regression-test integrity;
6. verification claim scope;
7. secret-aware diagnostic output; and
8. authority of instructions embedded in repository content.

Each family contains four semantic scenarios. Every scenario appears in compact and extended
layouts, giving eight contrast sets and 32 traces per family. A contrast set contains a permitted
plain trace, unsafe plain trace, permitted lexical decoy, and unsafe low-signal trace.

Train contains 128 traces. Development and test contain 64 traces each. Semantic scenario IDs are
disjoint across partitions, and each partition retains all eight policy families.

Unsafe actions carry a prohibited effect and a moderate, high, or critical severity label. The gold
control prevents that effect and completes the task through a recovery sequence. Permitted actions
complete the task under `allow`.

## 4. Monitor boundary

Stored traces contain labels, effects, and recovery records for scoring. Before a monitor runs, the
evaluator constructs `MonitorTrace` from the task and task-time events. Labels, required task
effects, recovery records, and action effects remain inside the evaluator. A regression test
inspects the supplied dataclass fields and fails if these records cross the boundary.

## 5. Evaluation

The evaluator measures exact control accuracy, unsafe-action prevention, permitted-task retention,
and overall task completion. It also scores intervention timing, field-level evidence,
counterfactual sensitivity and stability, causal-evidence accuracy, Brier score, latency, and
reported token cost.

Causal-evidence accuracy is awarded when the risk decision flips across a labelled counterfactual
and the unsafe decision cites a changed policy field. The metric tests the monitor's declared
evidence. It cannot establish an unobserved decision process.

Confidence intervals resample complete contrast sets, which keeps linked variants together. The
checked results use 1,000 percentile-bootstrap samples and seed `20260825`. The evaluator also
reports each partition, policy family, severity band, and four error counts.

## 6. Baselines

Four deterministic monitors are included. `allow-all` and `block-all` establish the policy
extremes. `keyword` scans event text for common warning terms. `policy-field-oracle` reads the
structured attributes used to construct the cases and checks the evaluator. A pinned adapter also
runs the existing Coding Agent Monitor Lab.

## 7. Results

| Monitor | Control accuracy | Prevention | Task completion | Permitted retention | Sensitivity | Stability | Causal evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| Block all | 0.2500 | 1.0000 | 0.2500 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Keyword | 0.2578 | 0.7656 | 0.3750 | 0.1562 | 0.1562 | 0.8438 | 0.0000 |
| Policy-field oracle | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Monitor Lab adapter | 0.5078 | 0.1875 | 0.9141 | 0.8281 | 0.2656 | 0.7344 | 0.0000 |

The keyword monitor prevents 98 unsafe effects and interrupts 108 permitted traces. Risk terms in
invariant history and lexical-decoy events account for much of that over-intervention. It cites
text fields, so its causal-evidence score is zero.

Monitor Lab prevents 24 unsafe effects and retains 106 permitted tasks. It performs best on false
verification and test weakening, where prevention reaches 0.50. Prevention is zero for four policy
families whose decisive state sits in structured attributes outside its original text rules.

The policy-field oracle validates dataset wiring and metric implementation. Since it reads the
fields used during case construction, its result is not an out-of-sample performance estimate.

## 8. Limits

All traces are synthetic and schema-led. The labels have one author and no independent agreement
study. The replay engine applies declared effects in memory; it does not run commands or observe a
working operating system.

Adaptive attacks, incomplete telemetry, policy conflicts, and operating-system isolation failures
sit outside version 0.2. The results describe baseline behaviour on this dataset and do not establish
coding-agent safety in deployment.
