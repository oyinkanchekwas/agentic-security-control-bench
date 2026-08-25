# Agentic Security Control Bench

A contrastive benchmark for testing whether coding-agent monitors base control decisions on
policy-relevant trace evidence.

The seed dataset contains 32 synthetic traces arranged in eight contrast sets. Each set changes a
small number of policy fields while keeping the coding task and surrounding events close. A
monitor must select a control, identify the first actionable event, and cite the fields supporting
its decision. The replay engine then checks whether the control prevents the prohibited effect and
preserves task completion.

## Quick start

The package has no runtime dependencies outside the Python standard library.

```bash
git clone https://github.com/oyinkanchekwas/agentic-security-control-bench.git
cd agentic-security-control-bench
make check
make baselines
```

Individual monitors can be evaluated from the command line:

```bash
PYTHONPATH=src python3 -m control_bench evaluate data/contrast_sets.jsonl \
  --monitor keyword --pretty
```

## Benchmark task

Every contrast set contains four traces:

- a permitted action with plain wording;
- an unsafe action with an explicit cue;
- a permitted action containing risky words as data; and
- an unsafe action expressed without the usual warning terms.

The paired structure tests whether a monitor responds to the policy state recorded in the trace.
It also exposes monitors that react mainly to words such as `delete`, `secret`, or `private`.

The current policy families cover filesystem scope, outbound destinations, publication approval,
dependency provenance, test integrity, verification claims, secret handling, and embedded
instructions.

## Measures

The evaluator reports:

- exact control accuracy;
- unsafe-action prevention and permitted-task retention;
- intervention-event accuracy and evidence-field precision/recall;
- counterfactual sensitivity and stability;
- causal-evidence accuracy;
- task completion after replay;
- Brier score, monitor latency, and token cost.

Definitions and denominators are recorded in [docs/BENCHMARK_PROTOCOL.md](docs/BENCHMARK_PROTOCOL.md).

## Included baselines

| Monitor | Control accuracy | Unsafe action prevention | Permitted task retention | Counterfactual sensitivity | Counterfactual stability | Causal evidence accuracy |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Allow all | 0.5000 | 0.0000 | 1.0000 | 0.0000 | 1.0000 | 0.0000 |
| Block all | 0.2500 | 1.0000 | 0.0000 | 0.0000 | 1.0000 | 0.0000 |
| Keyword | 0.2812 | 0.5625 | 0.3125 | 0.5000 | 0.5000 | 0.0000 |
| Policy field | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Monitor Lab adapter | 0.4375 | 0.1250 | 0.7500 | 0.2500 | 0.6250 | 0.0000 |

The policy-field monitor reads the labelled policy attributes used to construct the seed cases.
Its score checks the evaluator and replay path. It is an upper reference for this fixture set, with
no claim about performance on unseen traces.

Checked summaries are stored in [results/baselines.json](results/baselines.json) and
[results/monitor_lab.json](results/monitor_lab.json). The report in
[docs/RESULTS.md](docs/RESULTS.md) explains the observed failure patterns.
The full seed report is available in [report/technical_report.md](report/technical_report.md).

The optional Monitor Lab adapter keeps the earlier monitor implementation in the evaluation. Its
pinned source revision and local integration command are documented in
[docs/INPUT_CONTRACTS.md](docs/INPUT_CONTRACTS.md).

Case-level output can be generated without changing the committed summaries:

```bash
PYTHONPATH=src python3 -m control_bench compare data/contrast_sets.jsonl \
  --out results/raw/baselines.json --pretty
```

## Repository map

```text
data/                 contrast-set dataset
src/control_bench/    data model, monitors, replay engine, metrics, and CLI
tests/                dataset, replay, evaluator, and command-line tests
scripts/              deterministic data materialisation and repository checks
docs/                 protocol, data record, threat model, prior work, and results
results/              committed baseline output
report/               seed technical report
programme-lock.json    pinned Atlas and Monitor Lab source revisions
```

## Scope

The seed release is a controlled test fixture. It contains no private coding-agent logs, real
credentials, live endpoints, or executable attack payloads. Results from these 32 traces cannot be
used as evidence of deployment safety.

The prior-work review and the boundary of the present experiment are recorded in
[docs/PRIOR_WORK.md](docs/PRIOR_WORK.md).

## Licence

Code and synthetic data are released under the [MIT Licence](LICENSE).
