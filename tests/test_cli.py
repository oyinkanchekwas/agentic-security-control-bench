from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest

from control_bench.cli import main


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / "contrast_sets.jsonl"


class CliTests(unittest.TestCase):
    def test_validate_command(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            exit_code = main(["validate", str(DATASET)])
        self.assertEqual(exit_code, 0)
        self.assertIn("32 traces", output.getvalue())

    def test_compare_writes_json(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "comparison.json"
            with redirect_stdout(StringIO()):
                exit_code = main(["compare", str(DATASET), "--out", str(target), "--pretty"])
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
                    ]
                )
            self.assertEqual(exit_code, 0)
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertTrue(all("cases" not in result for result in payload["results"]))


if __name__ == "__main__":
    unittest.main()
