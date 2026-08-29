# Evidence-Grounded Control Decisions for Coding-Agent Traces

Oyinkansola Onwuchekwa

Version 0.4 report, 29 August 2026

## Abstract

Coding-agent monitors often return a risk score and prose explanation. Those outputs leave two
operational questions unresolved: which trace fields support the decision, and which control can
prevent a prohibited effect while preserving the task? This report presents a contrastive benchmark
that requires event-and-field evidence, a discrete control action, and a replay check. The ordinary
benchmark contains 320 synthetic traces across eight policy families, with disjoint semantic
scenarios for train, development, and test. Version 0.4 adds a separate 160-trace adversarial
holdout linked to frozen test counterparts.

Version 0.3 added a common five-field response, provider-payload isolation, execution-failure
accounting, paired interval estimates, and optional model adapters. A pinned 0.5B instruction model
was evaluated on 64 unseen test traces. It produced valid JSON on every case but collapsed to
`require_approval`, preventing every unsafe effect while retaining no permitted task.

The adversarial evaluation reproduces this failure over five perturbation classes. All 160 actions
are sent for approval, including 80 permitted actions. Unsafe prevention remains 1.0000, permitted
retention remains 0.0000, and selective utility is 0.0000.

## 1. Research question

A monitor can predict an unsafe label for the wrong reason. Keyword matching may flag a permitted
security fixture because it contains terms associated with secrets or deletion. The same rule may
miss an unsafe action written in ordinary operational language.

The benchmark asks whether a monitor responds to the policy-bearing difference between paired
traces, identifies the first event where intervention is possible, and cites the changed policy
field. Replayed effects then test whether the chosen control prevents harm and completes the task.

## 2. Relation to existing evaluations

AgentDojo evaluates security and utility under prompt injection. ControlArena supports online
monitoring and control protocols. MonitoringBench and SLEIGHT-Bench examine attacks that evade
coding-agent monitors. FixedBench studies action bias, and UnderSpecBench measures action-boundary
violations in underspecified DevOps tasks. StepShield and PASTABench study intervention timing,
while OSGuard combines contextual action labels with state-based checks.

This experiment concentrates on causal evidence at trace-field level and replayed task effects. The
prior-work table in `docs/PRIOR_WORK.md` records the review boundary and access date.

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

Each family contains five semantic scenarios. Every scenario appears in compact and extended
layouts, giving ten contrast sets and 40 traces per family. A contrast set contains a permitted
plain trace, unsafe plain trace, permitted lexical decoy, and unsafe low-signal trace.

Train and development contain 128 traces each. Test contains 64 traces drawn from a fifth scenario
per family that was added after the prompt was frozen. Semantic scenario identifiers are disjoint
across partitions, and every partition retains all eight policy families.

Unsafe actions carry a prohibited effect and a moderate, high, or critical severity label. The gold
control prevents that effect and completes the task through a recovery sequence. Permitted actions
complete the task under `allow`.

The v0.4 adversarial holdout contains 40 contrast sets and 160 traces. Every family has one set for
each of five perturbation classes. A set links to one v0.3 test trace and contains two
policy-preserving transformations plus two policy-changing transformations. The resulting labels
are balanced at 80 permitted and 80 unsafe.

## 4. Monitor boundary and response

Stored traces contain labels, effects, split membership, and recovery records for scoring. The
evaluator constructs `MonitorTrace` from the task and task-time events before a monitor runs. Gold
labels, expected controls, required task effects, recovery records, and action effects remain inside
the scorer.

Every monitor returns:

```json
{
  "control": "allow | warn | require_approval | block",
  "first_actionable_event": "event_id",
  "evidence_fields": ["field_path"],
  "confidence": 0.0,
  "reason": "brief explanation"
}
```

Validation rejects missing or extra keys, unknown controls, invalid confidence, unknown events, and
fields absent from the selected event. Failed validation, provider abstention, and provider errors
produce a fail-safe block with a separate execution status. Tests inspect provider payloads from
the single-pass judge and two-call investigator.

## 5. Evaluation

The evaluator measures exact control accuracy, unsafe-action prevention, permitted-task retention,
replayed task completion, intervention timing, field-level evidence, counterfactual sensitivity and
stability, causal-evidence accuracy, calibration, latency, tokens, estimated cost, abstention,
malformed output, and execution failure.

Adversarial evaluation adds clean-to-adversarial control consistency, appropriate decision change,
attack success, evidence and timing degradation, confidence shift, approval requests, intervention
burden, unnecessary intervention, and selective utility. Clean and adversarial scores remain in
separate result sections.

Causal-evidence accuracy is awarded when the risk decision flips across a labelled counterfactual
and the unsafe decision cites a changed policy field. The metric tests declared evidence. It cannot
establish an unobserved decision process.

Confidence intervals resample complete contrast sets, which keeps linked variants together. The
checked results use 1,000 percentile-bootstrap samples and seed `20260825`. Paired comparisons
resample the same sets for both monitors and report the metric difference. The Policy-field oracle
is excluded from those comparisons.

## 6. Monitors

`allow-all`, `block-all`, and `keyword` provide deterministic reference points. Version 0.4 adds
`approval-all` as a degenerate high-intervention reference. The Policy-field
oracle reads construction attributes and checks the evaluator ceiling. A pinned adapter runs the
existing Coding Agent Monitor Lab.

The checked learned baseline uses Qwen2.5-0.5B-Instruct through the optional Transformers adapter.
Its model revision, prompt, temperature, seed, and test split are fixed in
`configs/monitors/qwen2.5-0.5b-instruct.json`. Remote judge, two-call investigator, and
deterministic-model ensemble adapters are included without checked scores in this version.

## 7. Full-dataset results

| Monitor | Control accuracy | Prevention | Replayed completion | Permitted retention | Sensitivity | Stability | Causal evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| Block all | 0.3750 | 1.0000 | 0.3750 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Keyword | 0.3563 | 0.7562 | 0.4781 | 0.1562 | 0.1625 | 0.8375 | 0.0000 |
| Policy-field oracle | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Monitor Lab adapter | 0.5062 | 0.1750 | 0.9187 | 0.8375 | 0.2625 | 0.7375 | 0.0000 |

The keyword monitor prevents 121 unsafe effects and interrupts 135 permitted traces. Risk terms in
invariant history and lexical-decoy events account for much of that over-intervention. It cites
content fields, so its causal-evidence score is zero.

Monitor Lab prevents 28 unsafe effects and retains 134 permitted tasks. Its rules preserve more
utility, though prevention is limited where decisive policy state appears only in structured
attributes. The Policy-field oracle validates dataset wiring and metric implementation; it is not a
deployable competitor.

## 8. Held-out learned result

Qwen2.5 0.5B returns valid structured responses for all 64 test traces. It chooses
`require_approval` in every case, cites no evidence fields, and assigns confidence of at least 0.97.

| Measure | Result | 95% interval |
| --- | ---: | ---: |
| Control accuracy | 0.1250 | 0.0312 to 0.2500 |
| Unsafe-action prevention | 1.0000 | 1.0000 to 1.0000 |
| Replayed task completion | 0.1250 | 0.0312 to 0.2500 |
| Permitted-task retention | 0.0000 | 0.0000 to 0.0000 |
| Intervention-event accuracy | 0.3438 | 0.1250 to 0.5625 |
| Evidence F1 | 0.0000 | 0.0000 to 0.0000 |
| Brier score | 0.4982 | 0.4945 to 0.5001 |

The model gets the exact control on unsafe publication and dependency cases because those families
use `require_approval`. It gets no exact controls in the other six families and intervenes on every
permitted trace. Empty evidence fields produce zero evidence recall and zero causal-evidence
accuracy. Counterfactual sensitivity is zero because paired policy changes never alter its binary
decision.

Against the keyword monitor on the same test sets, Qwen has higher prevention by 0.2812, with a 95%
paired interval from 0.0625 to 0.5312. Its control-accuracy difference is -0.2188, permitted-retention
difference is -0.1562, and replayed-completion difference is -0.3594; all three paired intervals
exclude zero. Brier score is worse by 0.1208, with interval 0.0673 to 0.1670.

The result exposes a blanket-intervention failure pattern. Unsafe prevention alone would score the model
perfectly, while task replay, evidence, calibration, and paired counterfactual measures show that it
has not learned the intended policy boundary.

## 9. Adversarial robustness

The v0.4 holdout covers lexical decoys, policy-obscuring paraphrases, embedded instruction attacks,
multi-event composition, and deceptive completion or verification. Every trace records its clean
counterpart and changed field paths. The v0.3 data, prompts, model configuration, and checked result
hashes remain frozen.

| Monitor | Control accuracy | Prevention | Permitted retention | Approval rate | Burden | Selective utility |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.5000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 |
| Block all | 0.3750 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Approval all | 0.1250 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| Keyword | 0.3375 | 0.6625 | 0.1875 | 0.0000 | 0.7375 | 0.1875 |
| Monitor Lab | 0.5125 | 0.1250 | 0.9000 | 0.0000 | 0.1125 | 0.9000 |
| Qwen2.5 0.5B | 0.1250 | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |

Qwen returns a valid response for every adversarial trace and requests approval 160 times. It
records 80 unnecessary interventions. Appropriate decision change is 0.0000: the monitor keeps the
same control when the causal policy state changes. Evidence F1 is 0.0000, actionable-event accuracy
is 0.2750, and the Brier score is 0.4946.

The keyword monitor prevents 53 unsafe actions and interrupts 65 permitted actions. Monitor Lab
prevents 10 unsafe actions and retains 72 permitted tasks. Its interventions often attach to an
earlier decoy event, leaving actionable-event accuracy at 0.0000.

The Policy-field oracle scores 1.0000 on the causal decision and evidence measures. It is used only
to verify the scoring ceiling and remains excluded from deployable paired comparisons.

## 10. Limits

All traces are synthetic and schema-led. The labels have one author and no independent agreement
study. The replay engine applies declared effects in memory; it does not run commands or observe a
working operating system.

The learned results cover one small model under one frozen prompt. Adaptive attacks,
incomplete telemetry, policy conflicts, operating-system isolation failures, and collusion between
the monitored agent and monitor remain outside this benchmark. Synthetic adversarial robustness
does not establish deployment safety.
