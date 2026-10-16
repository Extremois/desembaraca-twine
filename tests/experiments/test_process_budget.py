"""Verify experimental process bounds without installing external layout engines."""

from pathlib import Path
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "experiments"))
from process_budget import ProcessLimitError, run_bounded


class ProcessBudgetTests(unittest.TestCase):
    def test_preserves_stdout_and_stderr(self):
        result = run_bounded([
            sys.executable, "-c",
            "import sys; sys.stdout.write('out'); sys.stderr.write('err')",
        ])
        self.assertEqual((result.returncode, result.stdout, result.stderr), (0, b"out", b"err"))

    def test_preserves_nonzero_exit_status(self):
        result = run_bounded([sys.executable, "-c", "raise SystemExit(7)"])
        self.assertEqual(result.returncode, 7)

    def test_stops_a_process_at_deadline(self):
        start = time.monotonic()
        with self.assertRaisesRegex(ProcessLimitError, "time"):
            run_bounded([sys.executable, "-c", "import time; time.sleep(10)"], timeout=0.2)
        self.assertLess(time.monotonic() - start, 3)

    def test_limits_combined_output_while_reading(self):
        with self.assertRaisesRegex(ProcessLimitError, "output"):
            run_bounded([
                sys.executable, "-c",
                "import sys; sys.stdout.buffer.write(b'x'*6000); sys.stderr.buffer.write(b'y'*6000)",
            ], max_output=8192)


if __name__ == "__main__":
    unittest.main()
