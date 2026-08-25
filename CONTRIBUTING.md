# Contributing

Please open an issue before changing the benchmark schema or gold controls. A useful proposal names
the policy rule, the prohibited effect, the least disruptive valid control, and the task effect
that must survive intervention.

New contrast sets should include two permitted traces and two unsafe traces. The set needs one
plain pair, one lexical decoy, one low-signal unsafe form, and declared causal fields. New semantic
scenarios must stay inside one dataset partition.

Run these checks before opening a pull request:

```bash
make check
```

Changes to Monitor Lab integration also require:

```bash
make integration
```

Do not add live credentials, private traces, executable attack payloads, or copied repository data.
Synthetic markers should be conspicuous and inert.

Explain why the change is needed in the commit body. Include any metric changes and identify the
dataset or evaluator behaviour that caused them.
