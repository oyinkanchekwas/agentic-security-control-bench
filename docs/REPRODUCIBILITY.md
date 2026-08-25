# Reproducing the Seed Results

## Environment

- Python 3.11 or later;
- no third-party runtime packages; and
- a POSIX shell for the `Makefile` commands.

## Commands

```bash
make data
make validate
make test
make baselines
make verify-results
make quality
```

`make data` rewrites `data/contrast_sets.jsonl` from the declarations in
`scripts/materialise_dataset.py`. `make baselines` rewrites `results/baselines.json`.

After both commands, `git diff --exit-code` should remain empty. A changed dataset or result file
means that the source declarations, evaluator, monitor code, or Python JSON serialisation has
changed. The included deterministic monitors report zero latency and token use, which keeps the
committed baseline file stable across machines.
