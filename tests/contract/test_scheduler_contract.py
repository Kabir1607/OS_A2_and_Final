"""Contract tests for library_sim.scheduler (owner: Kabir)."""

from __future__ import annotations

import random
import unittest

import tests  # noqa: F401
from library_sim.models import ReaderSpec, Scheduler
from library_sim.scheduler import ReadyQueue, fcfs_key, key_for, priority_key


def spec(pid: str, arrival: int, priority: int) -> ReaderSpec:
    return ReaderSpec(pid, arrival, priority, 1, "A")


class Keys(unittest.TestCase):
    def test_keys(self) -> None:
        s = spec("R7", 3, 2)
        self.assertEqual(fcfs_key(s), (3, "R7"))
        self.assertEqual(priority_key(s), (2, 3, "R7"))
        self.assertIs(key_for(Scheduler.FCFS), fcfs_key)
        self.assertIs(key_for(Scheduler.PRIORITY), priority_key)

    def test_ids_compare_as_strings(self) -> None:
        self.assertLess(fcfs_key(spec("R10", 0, 1)), fcfs_key(spec("R2", 0, 1)))


class ReadyQueueContract(unittest.TestCase):
    def test_pop_order_matches_sorted_keys(self) -> None:
        rng = random.Random(7)
        for scheduler in Scheduler:
            for _ in range(200):
                specs = [spec(f"R{i}", rng.randint(0, 5), rng.randint(1, 3))
                         for i in rng.sample(range(1, 30), rng.randint(1, 12))]
                q = ReadyQueue(scheduler)
                for s in specs:
                    q.push(s)
                popped = [q.pop() for _ in range(len(specs))]
                self.assertEqual(popped, sorted(specs, key=key_for(scheduler)))

    def test_insertion_order_never_matters(self) -> None:
        # A reader returning from BLOCKED_RESOURCE is re-pushed with its
        # ORIGINAL spec, so it lands in the same place as if it had never left.
        early, late = spec("R1", 0, 2), spec("R2", 5, 2)
        q = ReadyQueue(Scheduler.FCFS)
        q.push(late)
        q.push(early)
        self.assertEqual(q.pop(), early)

    def test_api(self) -> None:
        q = ReadyQueue(Scheduler.PRIORITY)
        self.assertEqual(len(q), 0)
        self.assertFalse(q)
        self.assertIsNone(q.peek())
        with self.assertRaises(IndexError):
            q.pop()
        a, b = spec("R1", 0, 2), spec("R2", 1, 1)
        q.push(a)
        q.push(b)
        self.assertTrue(q)
        self.assertEqual(len(q), 2)
        self.assertIn("R1", q)
        self.assertNotIn("R3", q)
        self.assertEqual(q.peek(), b)
        self.assertEqual(len(q), 2)            # peek doesn't remove
        with self.assertRaises(ValueError):
            q.push(a)                          # duplicate ID
        self.assertEqual(q.pop(), b)
        self.assertNotIn("R2", q)
        q.push(b)                              # re-push after pop is allowed
        self.assertEqual([q.pop(), q.pop()], [b, a])


if __name__ == "__main__":
    unittest.main()
