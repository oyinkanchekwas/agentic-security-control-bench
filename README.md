# Agentic Security Control Bench

A contrastive benchmark for testing whether coding-agent monitors base control decisions on
policy-relevant trace evidence.

Version 0.2 contains 256 synthetic traces in 64 contrast sets. Each monitor selects a control,
locates the first actionable event, and cites the fields supporting its decision. The replay engine
checks whether that control prevents the prohibited effect while preserving task completion.

`v0.2.0` | Python 3.11 and 3.12 | MIT Licence | 17 tests

## Checked results

| Monitor | Control accuracy | Unsafe prevention | Permitted retention | Sensitivity | Stability | Causal evidence |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.5000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| Block all | 0.2500 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Keyword | 0.2578 | 0.7656 | 0.1562 | 0.1562 | 0.8438 | 0.0000 |
| Policy-field oracle | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Monitor Lab adapter | 0.5078 | 0.1875 | 0.8281 | 0.2656 | 0.7344 | 0.0000 |

The keyword monitor prevents 98 of 128 unsafe effects and interrupts 108 of 128 permitted traces.
Monitor Lab retains 106 permitted tasks, though it prevents 24 unsafe effects. Both return text or
no evidence, so neither receives credit for the causal policy fields used by the paired cases.

![Unsafe-action prevention against permitted-task retention](docs/assets/safety-retention.svg)

The policy-field oracle reads the attributes used to construct the cases. Its score checks dataset
wiring, replay behaviour, and metric calculation. It is not a deployable monitor result.

Checked summaries, 95% bootstrap intervals, split metrics, and policy-family error counts are stored
in [results/baselines.json](results/baselines.json) and
[results/monitor_lab.json](results/monitor_lab.json). See
[docs/ERROR_ANALYSIS.md](docs/ERROR_ANALYSIS.md) for the count tables.

## Quick start

The package has no third-party runtime dependencies.

```bash
git clone https://github.com/oyinkanchekwas/agentic-security-control-bench.git
cd agentic-security-control-bench
make check
```

Run the keyword monitor on held-out scenarios:

```bash
PYTHONPATH=src python3 -m control_bench evaluate data/contrast_sets.jsonl \
  --monitor keyword --split test --summary-only --pretty
```

## Dataset design

Every contrast set contains four linked traces:

- a permitted action with plain wording;
- an unsafe action with an explicit cue;
- a permitted action containing risky words as data; and
- an unsafe action expressed without the usual warning terms.

Each semantic scenario has a compact four-event layout and an extended seven-event layout. The
extended form adds invariant history and status events. Scenarios remain disjoint across train,
development, and test: 128 train traces, 64 development traces, and 64 test traces.

The policy families cover filesystem scope, outbound destinations, publication approval,
dependency provenance, test integrity, verification claims, secret handling, and embedded
instructions. Unsafe cases carry moderate, high, or critical severity labels.

## Monitor boundary

Monitors receive `MonitorTrace`, which contains the task and task-time events. Gold labels,
required effects, recovery events, and action effects stay inside the evaluator. A boundary test
checks those exclusions before each repository release.

The decision interface accepts `allow`, `warn`, `revise`, `redact`, `request_approval`, `sandbox`,
and `block`. Monitor output also includes a risk score, event identifier, evidence fields, a brief
reason, latency, and token cost.

## Measures

The evaluator reports exact control accuracy, unsafe-action prevention, permitted-task retention,
task completion, intervention-event accuracy, evidence precision and recall, counterfactual
sensitivity and stability, causal-evidence accuracy, Brier score, latency, and token cost.

Intervals use 1,000 contrast-set bootstrap samples with a fixed seed. Results are also separated by
dataset partition, policy family, and severity. Definitions and denominators are recorded in
[docs/BENCHMARK_PROTOCOL.md](docs/BENCHMARK_PROTOCOL.md).

## Repository map

```text
data/                 versioned contrast sets and dataset manifest
src/control_bench/    data model, monitor boundary, replay engine, metrics, and CLI
tests/                dataset, isolation, replay, evaluator, and command-line tests
scripts/              materialisation, report generation, integration, and repository checks
docs/                 protocol, annotation guide, data record, threat model, and results
results/              checked baseline summaries
report/               technical report
programme-lock.json    pinned Atlas and Monitor Lab source revisions
```

## Scope

The dataset is synthetic. It contains no private coding-agent logs, real credentials, live
endpoints, or executable attack payloads. Its policy attributes are cleaner than working-agent
telemetry, and the labels have not undergone independent reviewer annotation. Scores from these
256 traces do not establish deployment safety.

The prior-work review and experimental boundary are recorded in
[docs/PRIOR_WORK.md](docs/PRIOR_WORK.md). Reproduction commands are in
[docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md).

## Licence

Code and synthetic data are released under the [MIT Licence](LICENSE).
