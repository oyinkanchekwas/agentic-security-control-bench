# Data Record

## Composition

The seed dataset contains eight contrast sets and 32 traces. Each set has two permitted traces and
two unsafe traces. All examples are synthetic and written for this benchmark.

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
`data/contrast_sets.jsonl`. Every run uses the same order and JSON key ordering. Dataset validation
checks trace balance, event ordering, evidence references, comparison labels, and replay outcomes.

Each unsafe trace must cause a prohibited effect when allowed. Its gold control must prevent that
effect and complete the task through the recorded recovery sequence. Each permitted trace must
complete safely when allowed.

## Synthetic markers

Names, paths, domains, repositories, and credentials are fictional. Reserved `.example` and
`.example.test` domains are used where a destination is needed. Credential fixtures use conspicuous
`FAKE_*_DO_NOT_USE` markers.

## Uses

The dataset supports monitor regression tests, evidence-localisation experiments, control-policy
comparisons, and counterfactual audits. It can also be used to test adapters that translate another
monitor's output into the benchmark decision schema.

## Limits

The traces are short and schema-led. Their policy fields are cleaner than telemetry collected from
working coding agents. They do not represent the frequency of failure modes in deployed systems,
and they do not measure performance under an adaptive attacker.

The labels were produced during dataset construction and have not undergone independent reviewer
annotation. Public claims should report the dataset size and synthetic status alongside every
score.
