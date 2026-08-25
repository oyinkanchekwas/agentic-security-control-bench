PYTHON ?= python3

.PHONY: data adversarial-data validate validate-adversarial test baselines adversarial-baselines verify-results verify-learned verify-adversarial reports quality package integration learned-qwen learned-adversarial-qwen check

data:
	PYTHONPATH=src $(PYTHON) scripts/materialise_dataset.py

adversarial-data:
	PYTHONPATH=src $(PYTHON) scripts/materialise_adversarial_suite.py

validate:
	PYTHONPATH=src $(PYTHON) -m control_bench validate data/contrast_sets.jsonl

validate-adversarial:
	PYTHONPATH=src $(PYTHON) -m control_bench validate-adversarial data/adversarial/contrast_sets.jsonl --clean data/contrast_sets.jsonl

test:
	PYTHONPATH=src $(PYTHON) -m unittest discover -s tests -v

baselines:
	PYTHONPATH=src $(PYTHON) -m control_bench compare data/contrast_sets.jsonl --out results/baselines.json --pretty --summary-only

adversarial-baselines:
	PYTHONPATH=src $(PYTHON) scripts/run_adversarial_baselines.py

verify-results:
	PYTHONPATH=src $(PYTHON) scripts/verify_results.py

verify-learned:
	PYTHONPATH=src $(PYTHON) scripts/verify_learned_result.py

verify-adversarial:
	PYTHONPATH=src $(PYTHON) scripts/verify_adversarial_results.py

reports:
	PYTHONPATH=src $(PYTHON) scripts/build_reports.py

quality:
	PYTHONPATH=src $(PYTHON) scripts/quality_gate.py

package:
	PIP_CACHE_DIR=/tmp/agentic-security-control-bench-pip-cache $(PYTHON) -m pip wheel . --no-deps --no-build-isolation --wheel-dir /tmp/agentic-security-control-bench-wheel

integration:
	PYTHONPATH=src:../coding-agent-monitor-lab/src $(PYTHON) scripts/verify_programme_links.py --atlas ../coding-agent-failure-atlas --monitor-lab ../coding-agent-monitor-lab
	PYTHONPATH=src:../coding-agent-monitor-lab/src $(PYTHON) scripts/run_monitor_lab_baseline.py
	PYTHONPATH=src:../coding-agent-monitor-lab/src $(PYTHON) scripts/run_adversarial_monitor_lab.py
	PYTHONPATH=src $(PYTHON) scripts/build_reports.py
	PYTHONPATH=src $(PYTHON) scripts/verify_adversarial_results.py

learned-qwen:
	PYTHONPATH=src $(PYTHON) scripts/run_learned_baseline.py --config configs/monitors/qwen2.5-0.5b-instruct.json --out results/qwen2.5-0.5b-instruct-test.json --raw-out results/raw/qwen2.5-0.5b-instruct-test.jsonl

learned-adversarial-qwen:
	PYTHONPATH=src $(PYTHON) scripts/run_adversarial_learned.py --config configs/monitors/qwen2.5-0.5b-instruct.json --out results/qwen2.5-0.5b-instruct-adversarial.json --raw-out results/raw/qwen2.5-0.5b-instruct-adversarial.jsonl

check: data adversarial-data validate validate-adversarial test baselines adversarial-baselines verify-results verify-learned verify-adversarial reports quality package
