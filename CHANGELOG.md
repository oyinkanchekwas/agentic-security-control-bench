# Changelog

## 0.4.0 - 2026-08-25

- Added a separate adversarial holdout with 40 contrast sets and 160 inert synthetic traces.
- Balanced five perturbation classes across all eight policy families.
- Linked every transformed trace to one frozen v0.3 test counterpart.
- Added clean-to-adversarial consistency, appropriate decision change, attack success, and confidence shift.
- Added approval-request, intervention-burden, unnecessary-intervention, and selective-utility measures.
- Added family-level and perturbation-level bootstrap intervals plus paired monitor differences.
- Evaluated deterministic baselines, Monitor Lab, and Qwen2.5-0.5B-Instruct on the adversarial set.
- Locked the v0.3 data, prompts, configuration, and result digests.

## 0.3.0 - 2026-08-25

- Replaced the seven-control decision object with a validated five-field response using four controls.
- Added fail-safe handling and separate counts for abstention, malformed output, and execution failure.
- Added optional local and remote model providers, a two-call investigator, and a deterministic-model ensemble.
- Added provider-payload isolation tests and ignored raw-response storage.
- Added input and output token counts, estimated cost, evidence F1, and replayed task completion.
- Added paired contrast-set bootstrap comparisons for monitors evaluated on the same traces.
- Added frozen run configurations and digest-bound learned-result verification.
- Evaluated Qwen2.5-0.5B-Instruct on the 64-trace held-out test split.

## 0.2.0 - 2026-08-25

- Expanded the dataset from 32 to 256 synthetic traces.
- Added disjoint train, development, and test scenarios.
- Added compact and extended event layouts with invariant distractor events.
- Added moderate, high, and critical severity labels.
- Restricted monitor inputs to task-time events and policy attributes.
- Renamed the policy-field reference as `policy-field-oracle`.
- Added per-split and per-policy-family metrics.
- Added deterministic 95% bootstrap intervals, error counts, and a results figure.

## 0.1.0 - 2026-08-25

- Added eight contrast sets covering eight coding-agent security policy families.
- Added deterministic monitors, replay checks, and Monitor Lab integration.
- Added repository tests and Python 3.11/3.12 checks.
- Added protocol, data, threat, prior-work, and results documentation.
