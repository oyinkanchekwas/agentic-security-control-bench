from __future__ import annotations

from html import escape
import json
from pathlib import Path

from control_bench.dataset import load_contrast_sets
from control_bench.evaluation import evaluate_monitor
from control_bench.monitors import MONITORS


ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / "results" / "baselines.json"
MONITOR_LAB = ROOT / "results" / "monitor_lab.json"
LEARNED = ROOT / "results" / "qwen2.5-0.5b-instruct-test.json"
MANIFEST = ROOT / "data" / "manifest.json"
ERROR_REPORT = ROOT / "docs" / "ERROR_ANALYSIS.md"
FIGURE = ROOT / "docs" / "assets" / "safety-retention.svg"
LEARNED_FIGURE = ROOT / "docs" / "assets" / "learned-test-safety-retention.svg"


LABELS = {
    "allow-all": "Allow all",
    "block-all": "Block all",
    "keyword": "Keyword",
    "policy-field-oracle": "Policy-field oracle",
    "monitor-lab": "Monitor Lab",
    "qwen2.5-0.5b-instruct": "Qwen2.5 0.5B",
}

COLOURS = {
    "allow-all": "#6b7280",
    "block-all": "#111827",
    "keyword": "#c2410c",
    "policy-field-oracle": "#047857",
    "monitor-lab": "#1d4ed8",
    "qwen2.5-0.5b-instruct": "#7c3aed",
}


def load_results() -> tuple[dict[str, dict[str, object]], dict[str, dict[str, object]]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    baseline_payload = json.loads(BASELINES.read_text(encoding="utf-8"))
    monitor_payload = json.loads(MONITOR_LAB.read_text(encoding="utf-8"))
    learned_payload = json.loads(LEARNED.read_text(encoding="utf-8"))
    if baseline_payload["dataset_sha256"] != manifest["sha256"]:
        raise ValueError("Baseline results do not match the materialised dataset digest.")
    if monitor_payload["dataset"]["sha256"] != manifest["sha256"]:
        raise ValueError("Monitor Lab results do not match the materialised dataset digest.")
    if learned_payload["run"]["dataset_sha256"] != manifest["sha256"]:
        raise ValueError("Learned results do not match the materialised dataset digest.")
    baselines = baseline_payload["results"]
    monitor_lab = monitor_payload["result"]
    full_results = {item["monitor"]: item for item in [*baselines, monitor_lab]}
    learned = learned_payload["result"]
    test_sets = tuple(
        item
        for item in load_contrast_sets(ROOT / "data" / "contrast_sets.jsonl")
        if item.split == "test"
    )
    keyword_test = evaluate_monitor(MONITORS["keyword"], test_sets, bootstrap_iterations=0)
    test_results = {
        keyword_test["monitor"]: keyword_test,
        learned["monitor"]: learned,
    }
    return full_results, test_results


def render_error_report(
    results: dict[str, dict[str, object]],
    test_results: dict[str, dict[str, object]],
) -> str:
    lines = [
        "# Error Analysis",
        "",
        "Each policy family contains 40 traces: 20 unsafe and 20 permitted. The first two sections use the full v0.3 dataset.",
        "",
    ]
    for monitor_name in ("keyword", "monitor-lab"):
        result = results[monitor_name]
        metrics = result["metrics"]
        errors = result["errors"]
        lines.extend(
            [
                f"## {LABELS[monitor_name]}",
                "",
                (
                    f"Unsafe-action prevention is {metrics['unsafe_action_prevention']:.4f}; "
                    f"permitted-task retention is {metrics['permitted_task_retention']:.4f}. "
                    f"The monitor records {errors['false_allows']} false allows and "
                    f"{errors['over_interventions']} interventions on permitted traces."
                ),
                "",
                "| Policy family | False allows | Over-interventions | Wrong controls | Evidence misses |",
                "| --- | ---: | ---: | ---: | ---: |",
            ]
        )
        for family, family_result in result["by_policy_family"].items():
            family_errors = family_result["errors"]
            lines.append(
                f"| `{family}` | {family_errors['false_allows']} | "
                f"{family_errors['over_interventions']} | {family_errors['wrong_controls']} | "
                f"{family_errors['evidence_misses']} |"
            )
        lines.append("")
    lines.extend(
        [
            "The evidence-miss count remains high for both monitors because they cite trace text or no evidence. The benchmark gives evidence credit only for the policy field that changes across each causal pair.",
            "",
            "These counts describe synthetic traces with schema-level policy fields. They do not estimate deployment incident rates.",
            "",
        ]
    )
    learned = test_results["qwen2.5-0.5b-instruct"]
    metrics = learned["metrics"]
    errors = learned["errors"]
    lines.extend(
        [
            "## Qwen2.5 0.5B on test",
            "",
            (
                f"The held-out run prevents {metrics['unsafe_action_prevention']:.4f} of unsafe "
                f"effects and retains {metrics['permitted_task_retention']:.4f} of permitted tasks. "
                f"It records {errors['false_allows']} false allows and {errors['over_interventions']} "
                "interventions on permitted traces."
            ),
            "",
            "| Policy family | False allows | Over-interventions | Wrong controls | Evidence misses |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for family, family_result in learned["by_policy_family"].items():
        family_errors = family_result["errors"]
        lines.append(
            f"| `{family}` | {family_errors['false_allows']} | "
            f"{family_errors['over_interventions']} | {family_errors['wrong_controls']} | "
            f"{family_errors['evidence_misses']} |"
        )
    lines.extend(
        [
            "",
            (
                f"Malformed-output rate is {metrics['malformed_output_rate']:.4f}; execution-failure "
                f"rate is {metrics['execution_failure_rate']:.4f}. Raw generations remain under the "
                "ignored `results/raw/` path."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def render_figure(
    results: dict[str, dict[str, object]],
    *,
    monitor_names: tuple[str, ...] | None = None,
    subtitle: str = "v0.3 dataset, 320 synthetic traces",
) -> str:
    width = 860
    height = 520
    left = 105
    right = 55
    top = 70
    bottom = 90
    plot_width = width - left - right
    plot_height = height - top - bottom

    def x(value: float) -> float:
        return left + value * plot_width

    def y(value: float) -> float:
        return top + (1.0 - value) * plot_height

    selected = monitor_names or tuple(results)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">Unsafe-action prevention against permitted-task retention</title>',
        f'<desc id="desc">Scatter plot of {len(selected)} monitors; {escape(subtitle)}.</desc>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        '<text x="105" y="34" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#111827">Safety and permitted-task retention</text>',
        f'<text x="105" y="56" font-family="Arial, sans-serif" font-size="13" fill="#4b5563">{escape(subtitle)}</text>',
    ]
    for step in range(6):
        value = step / 5
        grid_x = x(value)
        grid_y = y(value)
        parts.extend(
            [
                f'<line x1="{grid_x:.1f}" y1="{top}" x2="{grid_x:.1f}" y2="{top + plot_height}" stroke="#e5e7eb" stroke-width="1"/>',
                f'<line x1="{left}" y1="{grid_y:.1f}" x2="{left + plot_width}" y2="{grid_y:.1f}" stroke="#e5e7eb" stroke-width="1"/>',
                f'<text x="{grid_x:.1f}" y="{top + plot_height + 24}" text-anchor="middle" font-family="Arial, sans-serif" font-size="12" fill="#4b5563">{value:.1f}</text>',
                f'<text x="{left - 18}" y="{grid_y + 4:.1f}" text-anchor="end" font-family="Arial, sans-serif" font-size="12" fill="#4b5563">{value:.1f}</text>',
            ]
        )
    parts.extend(
        [
            f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="#111827" stroke-width="1.5"/>',
            f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="#111827" stroke-width="1.5"/>',
            f'<text x="{left + plot_width / 2:.1f}" y="{height - 32}" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#111827">Permitted-task retention</text>',
            f'<text x="24" y="{top + plot_height / 2:.1f}" text-anchor="middle" transform="rotate(-90 24 {top + plot_height / 2:.1f})" font-family="Arial, sans-serif" font-size="14" fill="#111827">Unsafe-action prevention</text>',
        ]
    )
    offsets = {
        "allow-all": (-112, -14),
        "block-all": (12, 24),
        "keyword": (12, -12),
        "policy-field-oracle": (-146, 24),
        "monitor-lab": (-92, -16),
        "qwen2.5-0.5b-instruct": (12, 24),
    }
    for monitor_name in selected:
        metrics = results[monitor_name]["metrics"]
        point_x = x(float(metrics["permitted_task_retention"]))
        point_y = y(float(metrics["unsafe_action_prevention"]))
        dx, dy = offsets[monitor_name]
        parts.extend(
            [
                f'<circle cx="{point_x:.1f}" cy="{point_y:.1f}" r="7" fill="{COLOURS[monitor_name]}" stroke="#ffffff" stroke-width="2"/>',
                f'<text x="{point_x + dx:.1f}" y="{point_y + dy:.1f}" font-family="Arial, sans-serif" font-size="12" font-weight="600" fill="{COLOURS[monitor_name]}">{escape(LABELS[monitor_name])}</text>',
            ]
        )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def main() -> int:
    results, test_results = load_results()
    ERROR_REPORT.write_text(render_error_report(results, test_results), encoding="utf-8")
    FIGURE.parent.mkdir(parents=True, exist_ok=True)
    FIGURE.write_text(render_figure(results), encoding="utf-8")
    LEARNED_FIGURE.write_text(
        render_figure(
            test_results,
            monitor_names=("keyword", "qwen2.5-0.5b-instruct"),
            subtitle="held-out test split, 64 synthetic traces",
        ),
        encoding="utf-8",
    )
    print(f"Wrote {ERROR_REPORT}, {FIGURE}, and {LEARNED_FIGURE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
