"""K10 cross-check (Kabir + Urvashi): with an effectively unlimited seat
pool, the A2 engine must reproduce the A1 port's START/COMPLETION for every
reader, and the same first five summary metrics.

Skipped until library_sim.engine and library_sim.memory exist.
"""

from __future__ import annotations

import importlib.util
import random
import unittest

from tests import REPO_ROOT
from library_sim.a1 import parse_a1_text, run_a1, to_reader_results
from library_sim.metrics import compute_process_metrics, compute_summary
from library_sim.models import Allocator, ReaderSpec, Scheduler, SimulationInput

HAVE_ENGINE = all(importlib.util.find_spec(f"library_sim.{m}") is not None
                  for m in ("engine", "memory"))
A1_ROOT = REPO_ROOT / "Assignment_1-OS_Lab_Python"


def a1_inputs() -> list[tuple[str, list[ReaderSpec]]]:
    cases = [(p.name, parse_a1_text(p.read_text()))
             for p in sorted((A1_ROOT / "tests" / "inputs").glob("*.txt"))]
    cases.append(("input.txt", parse_a1_text(
        (A1_ROOT / "input.txt").read_text())))
    rng = random.Random(2026)
    for i in range(200):
        n = rng.randint(1, 20)
        ids = rng.sample(range(1, 40), n)
        cases.append((f"random_{i}", [
            ReaderSpec(f"R{k}", rng.randint(0, rng.choice([0, 5, 40])), rng.randint(1, 4),
                       rng.randint(1, 12), "REGULAR")
            for k in ids
        ]))
    return cases


@unittest.skipUnless(HAVE_ENGINE, "needs library_sim.engine and library_sim.memory (Urvashi, Aarush)")
class EngineReproducesA1(unittest.TestCase):
    def test_unlimited_pool_matches_a1(self) -> None:
        from library_sim.engine import simulate

        for name, readers in a1_inputs():
            inp = SimulationInput(quantum=2, readers=tuple(readers))  # space_req = 1
            # Enough for EVERY reader at once: memory cannot delay admission.
            # This preserves the unlimited-pool check without scanning a million seats.
            unlimited_capacity = sum(r.space_req for r in readers)
            for scheduler in Scheduler:
                with self.subTest(input=name, scheduler=scheduler.value):
                    expected = {r.id: (r.start, r.completion)
                                for r in to_reader_results(run_a1(readers, scheduler))}
                    result = simulate(inp, scheduler, Allocator.FIRST_FIT, "A2",
                                      pool_capacity=unlimited_capacity)
                    actual = {r.id: (r.start, r.completion) for r in result.readers}
                    self.assertEqual(actual, expected)
                    self.assertEqual(result.incomplete, ())
                    exp_s = compute_summary(compute_process_metrics(
                        to_reader_results(run_a1(readers, scheduler))))
                    act_s = compute_summary(compute_process_metrics(result.readers))
                    for field in ("average_waiting", "average_turnaround", "average_response",
                                  "throughput", "service_utilization_pct"):
                        self.assertAlmostEqual(getattr(act_s, field), getattr(exp_s, field),
                                               places=9, msg=field)
                    self.assertEqual(act_s.blocked_for_memory_count, 0)


if __name__ == "__main__":
    unittest.main()
