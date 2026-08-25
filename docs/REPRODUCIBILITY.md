# Reproducing the v0.2 Results

The package requires Python 3.11 or later and a POSIX shell for the `Makefile` commands. It has no
third-party runtime packages.

Run the complete repository check:

```bash
make check
```

This command materialises the dataset and manifest, validates every trace, runs the tests,
recomputes the deterministic baselines, checks the stored metrics, rebuilds the error report and
figure, and runs the repository quality gate.

The evaluator uses 1,000 contrast-set bootstrap samples with seed `20260825`. The generated JSON
uses sorted keys, and the included monitors report zero latency and token use. A clean checkout
should therefore remain unchanged after `make check`:

```bash
git diff --exit-code
```

To evaluate the held-out test scenarios only:

```bash
PYTHONPATH=src python3 -m control_bench compare data/contrast_sets.jsonl \
  --split test --summary-only --pretty
```

The Monitor Lab result also depends on the source revision in `programme-lock.json`. With the
Failure Atlas and Monitor Lab checked out beside this repository, run:

```bash
make integration
```

`make integration` checks both source revisions, runs the adapter across all 256 traces, and
rebuilds the checked report files.
