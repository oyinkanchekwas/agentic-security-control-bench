# Evidence-Grounded Control Decisions for Coding-Agent Traces

Oyinkansola Onwuchekwa

Seed report, 25 August 2026

## Abstract

Coding-agent monitors often return a risk score and a prose explanation. Those outputs leave two
operational questions unresolved: which trace fields support the decision, and which control can
prevent harm while preserving the task? This report presents a contrastive benchmark protocol
that requires event-and-field evidence, a discrete control action, and a replay check. The seed
study contains 32 synthetic traces in eight contrast sets and evaluates four deterministic
baselines.

## 1. Problem

A monitor can produce the correct unsafe label for the wrong reason. Keyword matching may flag a
permitted security fixture because it contains terms associated with secrets or deletion. The same
monitor may miss an unsafe action written in ordinary operational language.

The benchmark tests decisions across controlled trace edits. A policy-bearing field changes
between permitted and unsafe variants, while decoy variants alter wording without changing the
policy state. The monitor is asked to identify the first actionable event and cite the precise
fields behind its control.

## 2. Relation to existing evaluations

AgentDojo evaluates security and utility under prompt injection. ControlArena supports online
monitoring and control protocols. MonitoringBench and SLEIGHT-Bench examine attacks that evade
coding-agent monitors. StepShield and PASTABench study intervention timing, while OSGuard combines
contextual action labels with state-based safety checks.

This experiment concentrates on causal evidence at the trace-field level. It combines contrastive
decision tests with replayed task effects. The prior-work table in `docs/PRIOR_WORK.md` records the
review boundary and access date.

## 3. Dataset

The dataset contains eight policy families:

1. filesystem workspace scope;
2. approved outbound destinations;
3. repository publication approval;
4. dependency source and revision checks;
5. regression-test integrity;
6. verification claim scope;
7. secret-aware diagnostic output; and
8. authority of instructions embedded in repository content.

Each family contains a permitted plain trace, unsafe plain trace, permitted lexical decoy, and
unsafe low-signal trace. This produces 16 permitted and 16 unsafe traces.

Unsafe actions carry at least one prohibited effect. The recorded gold control prevents that
effect, applies a recovery sequence, and completes the original task. Permitted actions complete
the task under `allow`.

## 4. Evaluation

The evaluator measures exact control accuracy, unsafe-action prevention, permitted-task retention,
and overall task completion. It also scores the first actionable event, field-level evidence,
counterfactual sensitivity, counterfactual stability, and causal-evidence accuracy. Risk-score
calibration is measured with the Brier score.

Causal-evidence accuracy is awarded when the risk decision flips across a labelled counterfactual
and the unsafe decision cites a changed policy field. The metric tests the monitor's declared
evidence. It cannot establish the internal cause of a model prediction.

## 5. Baselines

Four deterministic monitors are included in the benchmark package. `allow-all` and `block-all`
establish the two policy extremes. `keyword` scans event text for common warning terms.
`policy-field` reads the structured attributes used to label the fixture and acts as a reference
check for the evaluator. A pinned adapter also evaluates the existing Coding Agent Monitor Lab.

## 6. Results

| Monitor | Control accuracy | Prevention | Task completion | Permitted retention | Sensitivity | Stability | Causal evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| Block all | 0.2500 | 1.0000 | 0.2500 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Keyword | 0.2812 | 0.5625 | 0.5000 | 0.3125 | 0.5000 | 0.5000 | 0.0000 |
| Policy field | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Monitor Lab adapter | 0.4375 | 0.1250 | 0.8750 | 0.7500 | 0.2500 | 0.6250 | 0.0000 |

The keyword monitor loses permitted task retention because risky terms appear in contextual data.
Its sensitivity score also shows that half of the labelled policy changes fail to alter the binary
risk decision. Text-only evidence receives no credit against the gold structured fields.

Block-all prevents harm at the cost of every permitted task. Some unsafe tasks complete because
`block` is the recorded gold control for four policy families. The remaining unsafe tasks require
revision, redaction, approval, or isolation, so a blanket block prevents their recovery sequence.

The policy-field score validates dataset wiring and metric implementation. Since the monitor reads
the fields used during case construction, its result is not an out-of-sample performance estimate.

Monitor Lab was designed for text traces and excerpt-based findings. Its adapter prevents 12.5% of
unsafe effects and keeps 75% of permitted tasks. The result identifies a contract mismatch: policy
state held in structured action attributes is unavailable to its text-oriented rules and evidence
schema.

## 7. Limits

All traces are synthetic, short, and schema-led. The labels have one author and no independent
agreement study. The replay engine applies declared effects in memory; it does not run commands or
observe a real operating system. Adaptive attacks, long traces, missing telemetry, and conflicting
policies sit outside the seed study.

The current results establish that the protocol distinguishes several weak baselines. They do not
establish coding-agent safety or expected performance in deployment.
