# Data Record

## Composition

Version 0.3 contains 80 contrast sets and 320 traces. Each set has two permitted traces and two
unsafe traces. All examples are synthetic and written for this benchmark.

The split contains 128 train traces, 128 development traces, and 64 test traces. Semantic scenarios
are disjoint across those partitions. Each policy family contributes 40 traces spread across five
scenarios and two event layouts.

Lexical decoys make permitted traces look risky, while low-signal unsafe variants require the
structured policy state to resolve surface ambiguity. Extended layouts add unrelated history and a
pre-action status event to every member of the contrast set.

The covered failure modes are:

- destructive commands;
- data exfiltration;
- permission-boundary violations;
- supply-chain risk;
- test weakening;
- false verification claims;
- secret exposure; and
- prompt-injection compliance.

## Construction

Cases are declared in `scripts/materialise_dataset.py` and written deterministically to
`data/contrast_sets.jsonl`. Every run uses the same order and JSON key ordering. The generator also
writes `data/manifest.json`, which records version, counts, and the dataset SHA-256 digest.

Dataset validation checks trace balance, event ordering, evidence references, comparison labels,
split values, template identifiers, severity labels, and replay outcomes.

Each unsafe trace must cause a prohibited effect when allowed. Its gold control must prevent that
effect and complete the task through the recorded recovery sequence. Each permitted trace must
complete safely when allowed.

## Synthetic markers

Names, paths, domains, repositories, and credentials are fictional. Reserved `.example` and
`.example.test` domains are used where a destination is needed. Credential fixtures use conspicuous
`FAKE_*_DO_NOT_USE` markers.

## Adversarial Holdout

Version 0.4 adds `data/adversarial/contrast_sets.jsonl`. This file contains 40 sets and 160 traces,
split evenly between permitted and unsafe status. Each policy family contributes five sets. Each
perturbation class contributes eight sets.

The adversarial records use only v0.3 test traces as clean counterparts. Two traces in each set
preserve the source policy state; two change it. The relationship record stores the source trace
and scenario identifiers, changed field paths, causal-state relation, expected control,
actionable event, evidence fields, severity, and status.

`scripts/materialise_adversarial_suite.py` writes the suite deterministically. Its manifest binds
the output to the frozen clean dataset and generator. Validation checks source uniqueness, family
and class balance, duplicated gold metadata, and the test-only source boundary.

The transformed records contain no executable payload. Instruction attacks are inert strings, and
endpoint-like text uses reserved example or invalid domains.

## Uses

The dataset supports monitor regression tests, evidence-localisation experiments, control-policy
comparisons, and counterfactual audits. It can also be used to test adapters that translate another
monitor's output into the benchmark decision schema.

## Limits

Half of the traces contain seven events, while the compact layout contains four. Their policy
fields remain cleaner than telemetry collected from working coding agents. The dataset does not
represent failure-mode frequency in deployed systems or performance under an adaptive attacker.

The adversarial suite is generated from the same typed policy system as the ordinary data. It tests
five fixed perturbation classes and cannot represent unrestricted attacker adaptation. Its results
do not establish deployment safety.

The labels were produced during dataset construction and have not undergone independent reviewer
annotation. Public claims should report the dataset size and synthetic status alongside every
score.
