"""Evaluation tools for evidence-grounded coding-agent controls."""

from control_bench.dataset import load_contrast_sets, validate_contrast_sets
from control_bench.evaluation import evaluate_monitor
from control_bench.monitors import MONITORS

__all__ = ["MONITORS", "evaluate_monitor", "load_contrast_sets", "validate_contrast_sets"]
__version__ = "0.4.1"
