"""Contract tests for library_sim.a1 (owner: Kabir): the shared package's
A1 port must reproduce every C++ expected output byte for byte."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stderr, redirect_stdout

from tests import REPO_ROOT
from library_sim.a1 import a1_main, fcfs, priority_schedule, simulate_a1_text
from library_sim.models import ReaderSpec, Scheduler

CPP_TESTS = REPO_ROOT / "Assignment_1-OS_Lab_C++" / "tests"


class A1Regression(unittest.TestCase):
    def test_every_cpp_expected_output(self) -> None:
        inputs = sorted((CPP_TESTS / "inputs").glob("*.txt"))
        self.assertEqual(len(inputs), 10)
        for path in inputs:
            for scheduler in Scheduler:
                with self.subTest(input=path.name, algorithm=scheduler.value):
                    expected = (CPP_TESTS / "expected" / f"{path.stem}_{scheduler.value}.out").read_text()
                    self.assertEqual(simulate_a1_text(path.read_text(), scheduler), expected)

    def test_a1_main(self) -> None:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = a1_main([str(CPP_TESTS / "inputs" / "spec_sample.txt"), "FCFS"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), (CPP_TESTS / "expected" / "spec_sample_FCFS.out").read_text())
        for argv in ([], ["x.txt"], ["x.txt", "RR"], ["missing.txt", "FCFS"]):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                self.assertEqual(a1_main(argv), 1, argv)
            self.assertEqual(out.getvalue(), "")
            self.assertTrue(err.getvalue().startswith("Error: "))

    def test_results_cover_every_reader_once(self) -> None:
        readers = [ReaderSpec(f"R{i}", i % 3, 1 + i % 2, 2, "A") for i in range(7)]
        for run in (fcfs, priority_schedule):
            ids = sorted(r.spec.id for r in run(readers))
            self.assertEqual(ids, sorted(r.id for r in readers))


if __name__ == "__main__":
    unittest.main()
