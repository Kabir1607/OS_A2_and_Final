"""Command-line and end-of-run checks (U6, U7, U9a) that need only the A2 modules.

- a2_main writes the graded file and exits 0; bad arguments exit 1 with no output file.
- A resource-free Final run equals A2 plus RESOURCE_WAIT=0 and three CHECK lines (U9a),
  and does not need Samar's Final-only modules.
- The engine's end-of-run invariants (U6) fire if state is left behind.
"""

from __future__ import annotations

import importlib.util
import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

import tests  # noqa: F401  (puts src/ on sys.path)
from library_sim.models import Allocator, Scheduler

HAVE_ENGINE = all(importlib.util.find_spec(f"library_sim.{m}") is not None
                  for m in ("engine", "memory", "cli"))

SAMPLE = (
    "5\n2\n"
    "R1,0,2,5,REGULAR,4,0\n"
    "R2,1,1,3,REGULAR,3,0\n"
    "R3,2,3,2,REGULAR,1,0\n"
    "R4,3,1,4,REGULAR,2,0\n"
    "R5,4,2,1,REGULAR,6,0\n"
)


@unittest.skipUnless(HAVE_ENGINE, "engine.py, memory.py and cli.py are needed")
class CliAndInvariants(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.input = self.dir / "in.txt"
        self.input.write_text(SAMPLE, encoding="utf-8")

    def run_main(self, fn_name: str, argv: list[str]) -> tuple[int, str]:
        from library_sim import cli
        err = io.StringIO()
        with redirect_stderr(err):
            code = getattr(cli, fn_name)(argv)
        return code, err.getvalue()

    def test_a2_main_writes_graded_output(self) -> None:
        out = self.dir / "a2.txt"
        code, err = self.run_main("a2_main", [str(self.input), "PRIORITY", "FIRST_FIT", str(out)])
        self.assertEqual((code, err), (0, ""))
        text = out.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("PROCESS,R1,0,2,5,0,5,0,5,0,0,0,0\n"))
        self.assertIn("POOL,SPACE,6,6,72.7273,2\n", text)
        self.assertNotIn("CHECK", text)

    def test_bad_arguments_exit_1_without_output(self) -> None:
        out = self.dir / "never.txt"
        for argv in ([str(self.input), "RR", "FIRST_FIT", str(out)],
                     [str(self.input), "FCFS", "NEXT_FIT", str(out)],
                     [str(self.dir / "missing.txt"), "FCFS", "FIRST_FIT", str(out)],
                     [str(self.input), "FCFS"]):
            with self.subTest(argv=argv):
                code, err = self.run_main("a2_main", argv)
                self.assertEqual(code, 1)
                self.assertTrue(err.startswith("Error: "))
                self.assertNotIn("Traceback", err)
                self.assertFalse(out.exists())

    def test_resource_free_final_equals_a2(self) -> None:
        a2_out, final_out = self.dir / "a2.txt", self.dir / "final.txt"
        for scheduler in Scheduler:
            for allocator in Allocator:
                with self.subTest(scheduler=scheduler.value, allocator=allocator.value):
                    args = [str(self.input), scheduler.value, allocator.value]
                    self.assertEqual(self.run_main("a2_main", args + [str(a2_out)])[0], 0)
                    self.assertEqual(self.run_main("final_main", args + [str(final_out)])[0], 0)
                    a2_lines = a2_out.read_text(encoding="utf-8").splitlines()
                    expected = [line + ",0" if line.startswith("PROCESS,") else line
                                for line in a2_lines]
                    expected += ["CHECK,EXCLUSIVITY_VIOLATIONS,0",
                                 "CHECK,UNRESOLVED_DEADLOCKS,0",
                                 "CHECK,COMPLETED_COUNT,5"]
                    self.assertEqual(final_out.read_text(encoding="utf-8").splitlines(), expected)

    def test_missing_final_module_is_a_clean_error(self) -> None:
        if importlib.util.find_spec("library_sim.resource_parser") is not None:
            self.skipTest("resource_parser.py exists")
        res_input = self.dir / "res.txt"
        res_input.write_text("1\n1\nR1,0,1,3,REG,1,0\n1\nTEXTBOOK,1\n", encoding="utf-8")
        out = self.dir / "never.txt"
        code, err = self.run_main("final_main", [str(res_input), "FCFS", "FIRST_FIT", str(out)])
        self.assertEqual(code, 1)
        self.assertTrue(err.startswith("Error: "))
        self.assertFalse(out.exists())

    def test_end_of_run_invariant_fires_on_leftover_seats(self) -> None:
        from library_sim.engine import Simulation
        from library_sim.memory import SeatPool
        from library_sim.parser import parse_text

        # One reader, so the run still completes and the leftover seat is detectable.
        inp = parse_text("1\n1\nR1,0,1,3,REGULAR,2,0\n", "A2")
        sim = Simulation(inp, Scheduler.FCFS, Allocator.FIRST_FIT, mode="A2")
        # Simulate a memory bug: releases silently do nothing.
        with mock.patch.object(SeatPool, "release", lambda self, reader_id: (0, 0)):
            with self.assertRaisesRegex(AssertionError, "seats still occupied"):
                sim.run()


if __name__ == "__main__":
    unittest.main()
