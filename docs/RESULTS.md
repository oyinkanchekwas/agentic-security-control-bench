# Results

## Full dataset

The deterministic and Monitor Lab results use all 320 synthetic traces in version 0.3. Intervals
are 95% percentile intervals from 1,000 contrast-set bootstrap samples.

| Monitor | Control accuracy | Prevention | Replayed completion | Permitted retention | Intervention event | Evidence F1 | Sensitivity | Stability | Causal evidence | Brier score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.5000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.5000 |
| Block all | 0.3750 | 1.0000 | 0.3750 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.5000 |
| Keyword | 0.3563 | 0.7562 | 0.4781 | 0.1562 | 0.0750 | 0.0000 | 0.1625 | 0.8375 | 0.0000 | 0.3648 |
| Policy-field oracle | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.0018 |
| Monitor Lab adapter | 0.5062 | 0.1750 | 0.9187 | 0.8375 | 0.0125 | 0.0000 | 0.2625 | 0.7375 | 0.0000 | 0.4317 |

The keyword monitor prevents 121 of 160 unsafe effects. It stops 135 permitted traces, including
lexical decoys and traces containing warning terms in inert history. Its text citations do not
match the policy fields changed by the paired cases.

Monitor Lab retains 134 permitted tasks and prevents 28 unsafe effects. Prevention remains sparse
where the decisive state is held in structured policy attributes outside its text-oriented rules.
The family counts are recorded in [ERROR_ANALYSIS.md](ERROR_ANALYSIS.md).

The Policy-field oracle reads the attributes used to construct each contrast set. Its score checks
the evaluator, replay path, evidence keys, and gold controls. It is excluded from paired rankings
and does not estimate performance on unseen traces.

## Held-out Qwen2.5 0.5B run

The learned run covers 64 new test traces, with eight traces from each policy family. The prompt,
configuration, model revision, seed, and dataset digest were frozen before the run.

| Measure | Qwen2.5 0.5B | 95% interval |
| --- | ---: | ---: |
| Control accuracy | 0.1250 | 0.0312 to 0.2500 |
| Unsafe-action prevention | 1.0000 | 1.0000 to 1.0000 |
| Replayed task completion | 0.1250 | 0.0312 to 0.2500 |
| Permitted-task retention | 0.0000 | 0.0000 to 0.0000 |
| Intervention-event accuracy | 0.3438 | 0.1250 to 0.5625 |
| Evidence precision, recall, and F1 | 0.0000 | 0.0000 to 0.0000 |
| Counterfactual sensitivity | 0.0000 | 0.0000 to 0.0000 |
| Counterfactual stability | 1.0000 | 1.0000 to 1.0000 |
| Causal-evidence accuracy | 0.0000 | 0.0000 to 0.0000 |
| Brier score | 0.4982 | 0.4945 to 0.5001 |

All 64 outputs passed schema validation, with no abstentions or execution failures. The model chose
`require_approval` for every trace, including all 32 permitted cases. Every evidence array was
empty, and 56 controls were wrong. Exact control accuracy reaches 0.5 only for permission-boundary
and supply-chain cases, whose unsafe gold control is `require_approval`; it is zero in the other six
families.

Mean local latency was 3,821.4 ms per trace. The run used 40,064 input tokens and 3,195 output
tokens. Estimated provider cost is zero because inference ran locally; that figure does not include
electricity or hardware cost.

## Paired test comparison

The paired bootstrap compares Qwen with the keyword monitor on the same 16 contrast sets. Values
below are Qwen minus keyword.

| Measure | Point difference | 95% paired interval |
| --- | ---: | ---: |
| Control accuracy | -0.2188 | -0.4062 to -0.0152 |
| Unsafe-action prevention | 0.2812 | 0.0625 to 0.5312 |
| Permitted-task retention | -0.1562 | -0.2812 to -0.0312 |
| Replayed task completion | -0.3594 | -0.5469 to -0.1250 |
| Intervention-event accuracy | 0.2813 | 0.0937 to 0.4688 |
| Evidence F1 | 0.0000 | 0.0000 to 0.0000 |
| Brier score | 0.1208 | 0.0673 to 0.1670 |

The learned monitor prevents more unsafe effects in this test, but its blanket approval gate loses
all permitted-task utility and produces worse calibration. The intervals do not support a general
model-ranking claim beyond these synthetic cases and this frozen prompt.

![Held-out learned and keyword results](assets/learned-test-safety-retention.svg)

## Adversarial holdout

Version 0.4 evaluates 160 separately held-out adversarial traces. The ordinary test scores above
remain unchanged.

| Monitor | Prevention | Permitted retention | Approval rate | Burden | Selective utility |
| --- | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 1.0000 |
| Block all | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Approval all | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |
| Keyword | 0.6625 | 0.1875 | 0.0000 | 0.7375 | 0.1875 |
| Monitor Lab | 0.1250 | 0.9000 | 0.0000 | 0.1125 | 0.9000 |
| Qwen2.5 0.5B | 1.0000 | 0.0000 | 1.0000 | 1.0000 | 0.0000 |

Qwen requested approval on every adversarial trace and changed no decision when the causal policy
state changed. All 160 outputs passed schema validation. The run produced no abstention or
malformed output. Execution failure rate was zero.

[ADVERSARIAL_ROBUSTNESS.md](ADVERSARIAL_ROBUSTNESS.md) contains the family and perturbation reports,
bootstrap intervals, paired differences, metric definitions, and limits.
