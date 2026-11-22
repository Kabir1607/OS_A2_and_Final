"""Tests for the A1 Python port.

Run from the Assignment_1-OS_Lab_Python directory:
    python3 -m unittest discover -s tests -v
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from library_sim.a1 import (  # noqa: E402
    fcfs, parse_a1_text, priority_schedule, simulate_a1_text,
)
from library_sim.errors import InputError  # noqa: E402
from library_sim.metrics import compute_process_metrics, compute_summary  # noqa: E402
from library_sim.models import (  # noqa: E402
    LEGAL_TRANSITIONS, STANDARD_RESOURCES, Reader, ReaderResult, ReaderSpec,
    Scheduler, State,
)
from library_sim.output import fmt_decimal  # noqa: E402
from library_sim.scheduler import ReadyQueue  # noqa: E402

INPUTS = ROOT / "tests" / "inputs"
EXPECTED = ROOT / "tests" / "expected"


class RegressionAgainstCpp(unittest.TestCase):
    """Every C++ expected output must be reproduced byte for byte."""

    def test_every_expected_output(self) -> None:
        cases = sorted(INPUTS.glob("*.txt"))
        self.assertEqual(len(cases), 10)
        for input_path in cases:
            for scheduler in Scheduler:
                with self.subTest(input=input_path.name, algorithm=scheduler.value):
                    expected = (EXPECTED / f"{input_path.stem}_{scheduler.value}.out").read_text()
                    actual = simulate_a1_text(input_path.read_text(), scheduler)
                    self.assertEqual(actual, expected)

    def test_cli_matches_expected(self) -> None:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "main.py"), str(INPUTS / "spec_sample.txt"), "PRIORITY"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(proc.stdout, (EXPECTED / "spec_sample_PRIORITY.out").read_text())
        self.assertEqual(proc.stderr, "")


class CliErrors(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(ROOT / "main.py"), *args],
                              capture_output=True, text=True, check=False)

    def test_wrong_argument_count(self) -> None:
        proc = self.run_cli(str(INPUTS / "spec_sample.txt"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("Usage", proc.stderr)
        self.assertEqual(proc.stdout, "")

    def test_unknown_algorithm(self) -> None:
        proc = self.run_cli(str(INPUTS / "spec_sample.txt"), "fcfs")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("FCFS or PRIORITY", proc.stderr)

    def test_missing_file(self) -> None:
        proc = self.run_cli("does_not_exist.txt", "FCFS")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("cannot open", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)

    def test_malformed_file(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("2\n2\nR1,0,1,3,REGULAR\n")
        proc = self.run_cli(f.name, "FCFS")
        Path(f.name).unlink()
        self.assertEqual(proc.returncode, 1)
        self.assertIn("expected 2 reader rows", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)


class Parsing(unittest.TestCase):
    def assert_error(self, text: str, fragment: str, line_no: int | None = None) -> None:
        with self.assertRaises(InputError) as ctx:
            parse_a1_text(text)
        self.assertIn(fragment, str(ctx.exception))
        if line_no is not None:
            self.assertEqual(ctx.exception.line_no, line_no)

    def test_valid_with_crlf_and_trailing_blank_lines(self) -> None:
        readers = parse_a1_text("2\r\n2\r\nR2,1,1,4,FACULTY\r\nR1,0,3,7,REGULAR\r\n\r\n\n")
        self.assertEqual([r.id for r in readers], ["R2", "R1"])   # file order kept
        self.assertEqual(readers[1], ReaderSpec("R1", 0, 3, 7, "REGULAR"))

    def test_errors(self) -> None:
        self.assert_error("", "empty")
        self.assert_error("0\n2\n", "N must be at least 1", 1)
        self.assert_error("x\n2\n", "N must be an integer", 1)
        self.assert_error("1\n", "missing the quantum", 2)
        self.assert_error("1\n0\nR1,0,1,1,A\n", "Q must be at least 1", 2)
        self.assert_error("2\n2\nR1,0,1,1,A\n", "expected 2 reader rows")
        self.assert_error("1\n2\nR1,0,1,1\n", "expected ID,ARRIVAL", 3)
        self.assert_error("2\n2\nR1,0,1,1,A\nR1,1,1,1,A\n", "duplicate reader ID R1", 4)
        self.assert_error("1\n2\nR 1,0,1,1,A\n", "invalid reader ID", 3)
        self.assert_error("1\n2\nR1,-1,1,1,A\n", "ARRIVAL must be >= 0", 3)
        self.assert_error("1\n2\nR1,0,0,1,A\n", "PRIORITY must be >= 1", 3)
        self.assert_error("1\n2\nR1,0,1,0,A\n", "SERVICE must be >= 1", 3)
        self.assert_error("1\n2\nR1,0,1,two,A\n", "SERVICE must be an integer", 3)
        self.assert_error("1\n2\nR1,0,1,1,\n", "CATEGORY must not be empty", 3)


class Scheduling(unittest.TestCase):
    def test_lexicographic_ids(self) -> None:
        readers = [ReaderSpec("R2", 0, 1, 1, "A"), ReaderSpec("R10", 0, 1, 1, "A"),
                   ReaderSpec("R1", 0, 1, 1, "A")]
        order = [r.spec.id for r in fcfs(readers)]
        self.assertEqual(order, ["R1", "R10", "R2"])          # string order: R10 < R2

    def test_priority_beats_arrival(self) -> None:
        # Librarians free up at t=5 and t=6; R3 arrived first, R4 has the better priority.
        readers = [ReaderSpec("R1", 0, 1, 5, "A"), ReaderSpec("R2", 0, 1, 6, "A"),
                   ReaderSpec("R3", 1, 3, 1, "A"), ReaderSpec("R4", 2, 1, 1, "A")]
        by_id = {r.spec.id: r for r in priority_schedule(readers)}
        self.assertEqual((by_id["R4"].start, by_id["R3"].start), (5, 6))
        by_id = {r.spec.id: r for r in fcfs(readers)}
        self.assertEqual((by_id["R3"].start, by_id["R4"].start), (5, 6))

    def test_idle_gap(self) -> None:
        readers = [ReaderSpec("R1", 10, 1, 2, "A")]
        for run in (fcfs, priority_schedule):
            self.assertEqual((run(readers)[0].start, run(readers)[0].completion), (10, 12))


class ReadyQueueTests(unittest.TestCase):
    def test_fcfs_and_priority_order(self) -> None:
        specs = [ReaderSpec("R2", 1, 1, 1, "A"), ReaderSpec("R10", 1, 2, 1, "A"),
                 ReaderSpec("R1", 2, 1, 1, "A")]
        fq, pq = ReadyQueue(Scheduler.FCFS), ReadyQueue(Scheduler.PRIORITY)
        for s in specs:
            fq.push(s)
            pq.push(s)
        self.assertEqual([fq.pop().id for _ in range(3)], ["R10", "R2", "R1"])
        self.assertEqual([pq.pop().id for _ in range(3)], ["R2", "R1", "R10"])

    def test_queue_api(self) -> None:
        q = ReadyQueue(Scheduler.FCFS)
        self.assertFalse(q)
        self.assertIsNone(q.peek())
        with self.assertRaises(IndexError):
            q.pop()
        spec = ReaderSpec("R1", 0, 1, 1, "A")
        q.push(spec)
        self.assertIn("R1", q)
        self.assertEqual(len(q), 1)
        with self.assertRaises(ValueError):
            q.push(spec)
        self.assertEqual(q.peek(), spec)
        self.assertEqual(q.pop(), spec)
        self.assertNotIn("R1", q)


class ModelsAndMetrics(unittest.TestCase):
    def test_lifecycle_transitions(self) -> None:
        reader = Reader(ReaderSpec("R1", 0, 1, 1, "A"))
        for state in (State.READY, State.RUNNING, State.TERMINATED):
            reader.transition(state)
        self.assertIs(reader.state, State.TERMINATED)
        with self.assertRaises(AssertionError):
            Reader(ReaderSpec("R2", 0, 1, 1, "A")).transition(State.RUNNING)
        self.assertEqual(set(LEGAL_TRANSITIONS), set(State))

    def test_standard_resources(self) -> None:
        self.assertEqual(len(STANDARD_RESOURCES), 17)
        self.assertIn("OS_BOOK_10", STANDARD_RESOURCES)
        self.assertIn("REFERENCE_BOOK", STANDARD_RESOURCES)

    def test_a2_style_metrics(self) -> None:
        # A=0, M=2, S=5, C=9, B=3, resource wait 1 -> waiting 6 = 2 + 3 + 1.
        m = compute_process_metrics([ReaderResult("R1", 0, 1, 3, 5, 9, 2, 1)])[0]
        self.assertEqual((m.waiting, m.mem_wait, m.ready_wait, m.resource_wait), (6, 2, 3, 1))
        summary = compute_summary([m])
        self.assertEqual(summary.blocked_for_memory_count, 1)
        self.assertAlmostEqual(summary.average_memory_wait, 2.0)
        self.assertEqual(fmt_decimal(11 / 3), "3.6667")
        self.assertEqual(fmt_decimal(75), "75.0000")

    def test_inconsistent_timestamps_rejected(self) -> None:
        with self.assertRaises(AssertionError):
            compute_process_metrics([ReaderResult("R1", 5, 1, 3, 4, 7, 5)])   # S < A


if __name__ == "__main__":
    unittest.main()
