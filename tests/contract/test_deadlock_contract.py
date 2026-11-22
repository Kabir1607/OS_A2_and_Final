"""Contract tests for library_sim.deadlock (owner: Samar).

Covers S6 and S6b.
"""

from __future__ import annotations

import importlib.util
import unittest

import tests  # noqa: F401
from library_sim.deadlock import (
    UNSAFE_DEMO_INPUT,
    PreventionPolicy,
    find_cycles,
    resource_rank,
    run_blocking_demo,
    run_unsafe_demo,
)
from library_sim.models import Allocator, Scheduler

HAVE_MEMORY = importlib.util.find_spec("library_sim.memory") is not None


class DeadlockContract(unittest.TestCase):
    def test_find_cycles_no_cycle(self) -> None:
        graph = {"R1": ["R2"], "R2": ["R3"], "R3": []}
        self.assertEqual(find_cycles(graph), [])

    def test_find_cycles_two_cycle_rotated(self) -> None:
        # R2 -> R1 -> R2
        graph = {"R2": ["R1"], "R1": ["R2"]}
        cycles = find_cycles(graph)
        self.assertEqual(cycles, [["R1", "R2"]])

    def test_find_cycles_three_cycle(self) -> None:
        graph = {"R3": ["R1"], "R1": ["R2"], "R2": ["R3"]}
        cycles = find_cycles(graph)
        self.assertEqual(cycles, [["R1", "R2", "R3"]])

    def test_find_cycles_multiple_independent_cycles(self) -> None:
        graph = {
            "R2": ["R1"],
            "R1": ["R2"],
            "R4": ["R3"],
            "R3": ["R4"],
        }
        cycles = find_cycles(graph)
        self.assertEqual(cycles, [["R1", "R2"], ["R3", "R4"]])

    def test_resource_rank(self) -> None:
        declared = ["OS_BOOK_2", "OS_BOOK_10", "JOURNAL"]
        # Alphabetical: JOURNAL (0), OS_BOOK_10 (1), OS_BOOK_2 (2)
        self.assertEqual(resource_rank("JOURNAL", declared), 0)
        self.assertEqual(resource_rank("OS_BOOK_10", declared), 1)
        self.assertEqual(resource_rank("OS_BOOK_2", declared), 2)

    def test_run_unsafe_demo_three_policies(self) -> None:
        if not HAVE_MEMORY:
            reports = run_unsafe_demo(
                policies=(
                    PreventionPolicy.NONE,
                    PreventionPolicy.ROLLBACK,
                    PreventionPolicy.ORDERED,
                ),
                input_path=UNSAFE_DEMO_INPUT,
                scheduler=Scheduler.FCFS,
                allocator=Allocator.FIRST_FIT,
            )
            self.assertEqual(len(reports), 3)
            return

        reports = run_unsafe_demo(
            policies=(
                PreventionPolicy.NONE,
                PreventionPolicy.ROLLBACK,
                PreventionPolicy.ORDERED,
            ),
            input_path=UNSAFE_DEMO_INPUT,
            scheduler=Scheduler.FCFS,
            allocator=Allocator.FIRST_FIT,
        )
        self.assertEqual(len(reports), 3)

        # NONE should detect deadlock and stop
        r_none = reports[0]
        self.assertEqual(r_none.policy, PreventionPolicy.NONE)
        self.assertTrue(r_none.deadlocked)
        self.assertEqual(r_none.cycle, ("R1", "R2"))
        self.assertEqual(len(r_none.completed), 0)

        # ROLLBACK should complete without deadlock
        r_rollback = reports[1]
        self.assertEqual(r_rollback.policy, PreventionPolicy.ROLLBACK)
        self.assertFalse(r_rollback.deadlocked)
        self.assertEqual(sorted(r_rollback.completed), ["R1", "R2"])
        self.assertGreater(r_rollback.result.policy_stats.rollbacks, 0)

        # ORDERED should complete without deadlock
        r_ordered = reports[2]
        self.assertEqual(r_ordered.policy, PreventionPolicy.ORDERED)
        self.assertFalse(r_ordered.deadlocked)
        self.assertEqual(sorted(r_ordered.completed), ["R1", "R2"])

    def test_run_blocking_demo(self) -> None:
        rep = run_blocking_demo(timeout_s=0.2)
        self.assertEqual(rep.policy, PreventionPolicy.NONE)
        self.assertTrue(rep.deadlocked)
        self.assertEqual(rep.cycle, ("R1", "R2"))


if __name__ == "__main__":
    unittest.main()
