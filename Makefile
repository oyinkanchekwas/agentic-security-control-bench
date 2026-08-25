.PHONY: data validate test baselines verify-results reports quality integration check

data:
	PYTHONPATH=src python3 scripts/materialise_dataset.py

validate:
	PYTHONPATH=src python3 -m control_bench validate data/contrast_sets.jsonl

test:
	PYTHONPATH=src python3 -m unittest discover -s tests -v

baselines:
	PYTHONPATH=src python3 -m control_bench compare data/contrast_sets.jsonl --out results/baselines.json --pretty --summary-only

verify-results:
	PYTHONPATH=src python3 scripts/verify_results.py

reports:
	PYTHONPATH=src python3 scripts/build_reports.py

quality:
	PYTHONPATH=src python3 scripts/quality_gate.py

integration:
	PYTHONPATH=src:../coding-agent-monitor-lab/src python3 scripts/verify_programme_links.py --atlas ../coding-agent-failure-atlas --monitor-lab ../coding-agent-monitor-lab
	PYTHONPATH=src:../coding-agent-monitor-lab/src python3 scripts/run_monitor_lab_baseline.py
	PYTHONPATH=src python3 scripts/build_reports.py

check: data validate test baselines verify-results reports quality
