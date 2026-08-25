# Reproducing the v0.4 Results

The package requires Python 3.11 or later and a POSIX shell for the `Makefile` commands. It has no
third-party runtime packages for deterministic evaluation.

Run the complete repository check:

```bash
make check
```

This command materialises the ordinary and adversarial datasets, validates every trace, runs the
tests, recomputes both deterministic result files, checks the stored learned summaries, rebuilds
the reports, runs the repository quality gate, and builds a wheel.

The evaluator uses 1,000 contrast-set bootstrap samples with seed `20260825`. Generated JSON uses
sorted keys. Included deterministic monitors and Monitor Lab record zero benchmark latency because
timing short in-process rules is dominated by host noise. A clean checkout should remain unchanged
after `make check`:

```bash
git diff --exit-code
```

To evaluate the held-out test scenarios only:

```bash
PYTHONPATH=src python3 -m control_bench compare data/contrast_sets.jsonl \
  --split test --summary-only --pretty
```

To evaluate the separate adversarial holdout:

```bash
PYTHONPATH=src python3 -m control_bench compare-adversarial \
  data/adversarial/contrast_sets.jsonl \
  --clean data/contrast_sets.jsonl --summary-only --pretty
```

The adversarial manifest records the suite digest, clean v0.3 digest, generator digest, and balance
counts. `configs/v0.3-frozen.json` records the earlier data, prompts, configuration, and result
hashes. Validation fails if a clean counterpart falls outside the v0.3 test split.

The Monitor Lab result also depends on the source revision in `programme-lock.json`. With the
Failure Atlas and Monitor Lab checked out beside this repository, run:

```bash
make integration
```

`make integration` checks both source revisions, runs the adapter across all 320 ordinary traces
and 160 adversarial traces, rebuilds the checked report files, and verifies the stored adversarial
summary.

## Local instruction model

Install the separate local-model extra in an isolated environment:

```bash
python3.11 -m venv .venv-model
.venv-model/bin/pip install -e '.[local-model]'
```

The checked held-out run uses the pinned configuration in
`configs/monitors/qwen2.5-0.5b-instruct.json`. It expects the recorded model revision to be present
in the local model cache:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  make PYTHON=.venv-model/bin/python learned-qwen
```

Run the same frozen monitor on the adversarial holdout with:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  make PYTHON=.venv-model/bin/python learned-adversarial-qwen
```

The command writes a committed summary and ignored case-level provider records. Running the model
again updates its timestamp and latency. Dataset, prompt, configuration, model identifier, and
model revision remain fixed in the run record.

## Remote and investigator monitors

Install `.[remote-model]`, create a local configuration outside version control, and set its model
identifier, endpoint, and cost rates. Put the access credential in the environment
variable named by the configuration. The same runner supports the single-pass judge, two-call
investigator, and deterministic-model ensemble.
