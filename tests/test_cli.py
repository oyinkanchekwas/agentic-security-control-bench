from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from control_bench.cli import main


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "contrast_sets.jsonl"
ADVERSARIAL = ROOT / "data" / "adversarial" / "contrast_sets.jsonl"


class CliTests(unittest.TestCase):
    def test_validate_command(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["validate", str(DATASET)])
        self.assertEqual(exit_code, 0)
        self.assertIn("320 traces", output.getvalue())

    def test_compare_writes_json(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "comparison.json"
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "compare",
                        str(DATASET),
                        "--out",
                        str(target),
                        "--pretty",
                        "--bootstrap-iterations",
                        "20",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["results"]), 4)

    def test_summary_output_omits_case_records(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "summary.json"
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "compare",
                        str(DATASET),
                        "--out",
                        str(target),
                        "--summary-only",
                        "--bootstrap-iterations",
                        "20",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertTrue(all("cases" not in result for result in payload["results"]))

    def test_split_filter_uses_held_out_cases(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "test-summary.json"
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "evaluate",
                        str(DATASET),
                        "--monitor",
                        "keyword",
                        "--split",
                        "test",
                        "--summary-only",
                        "--bootstrap-iterations",
                        "20",
                        "--out",
                        str(target),
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(payload["case_count"], 64)

    def test_validate_adversarial_command(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(
                [
                    "validate-adversarial",
                    str(ADVERSARIAL),
                    "--clean",
                    str(DATASET),
                ]
            )
        self.assertEqual(exit_code, 0)
        self.assertIn("160 traces", output.getvalue())

    def test_adversarial_summary_omits_case_records(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "adversarial-summary.json"
            with redirect_stdout(StringIO()):
                exit_code = main(
                    [
                        "compare-adversarial",
                        str(ADVERSARIAL),
                        "--clean",
                        str(DATASET),
                        "--out",
                        str(target),
                        "--summary-only",
                        "--bootstrap-iterations",
                        "0",
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(len(payload["results"]), 5)
            self.assertTrue(all("cases" not in result for result in payload["results"]))


if __name__ == "__main__":
    unittest.main()
