PYTHON ?= python3

.PHONY: data validate test baselines verify-results verify-learned reports quality package integration learned-qwen check

data:
	PYTHONPATH=src $(PYTHON) scripts/materialise_dataset.py

validate:
	PYTHONPATH=src $(PYTHON) -m control_bench validate data/contrast_sets.jsonl

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

baselines:
	PYTHONPATH=src $(PYTHON) -m control_bench compare data/contrast_sets.jsonl --out results/baselines.json --pretty --summary-only

verify-results:
	PYTHONPATH=src $(PYTHON) scripts/verify_results.py

verify-learned:
	PYTHONPATH=src $(PYTHON) scripts/verify_learned_result.py

reports:
	PYTHONPATH=src $(PYTHON) scripts/build_reports.py

quality:
	PYTHONPATH=src $(PYTHON) scripts/quality_gate.py

package:
	PIP_CACHE_DIR=/tmp/agentic-security-control-bench-pip-cache $(PYTHON) -m pip wheel . --no-deps --no-build-isolation --wheel-dir /tmp/agentic-security-control-bench-wheel

integration:
	PYTHONPATH=src:../coding-agent-monitor-lab/src $(PYTHON) scripts/verify_programme_links.py --atlas ../coding-agent-failure-atlas --monitor-lab ../coding-agent-monitor-lab
	PYTHONPATH=src:../coding-agent-monitor-lab/src $(PYTHON) scripts/run_monitor_lab_baseline.py
	PYTHONPATH=src $(PYTHON) scripts/build_reports.py

learned-qwen:
	PYTHONPATH=src $(PYTHON) scripts/run_learned_baseline.py --config configs/monitors/qwen2.5-0.5b-instruct.json --out results/qwen2.5-0.5b-instruct-test.json --raw-out results/raw/qwen2.5-0.5b-instruct-test.jsonl

check: data validate test baselines verify-results verify-learned reports quality package
