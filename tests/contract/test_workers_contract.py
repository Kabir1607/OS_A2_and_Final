"""Contract tests for WorkerPool (owner: Samar).

Covers S5, S5b, and S6c.
"""

from __future__ import annotations

import unittest

import tests  # noqa: F401
from library_sim.deadlock import PreventionPolicy
from library_sim.models import Action, ActionType, ResourceSpec
from library_sim.resources import ResourceManager
from library_sim.trace import Tracer
from library_sim.workers import ActionBatch, BatchResult, WorkerPool
from tests.fakes.fake_workers import WorkerPool as FakeWorkerPool


class BaseWorkersContract(unittest.TestCase):
    def create_pool(self, manager: ResourceManager) -> WorkerPool | FakeWorkerPool:
        return WorkerPool(manager, num_workers=2)

    def test_run_batches_order_preserved(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1), ResourceSpec("REFERENCE_BOOK", 1)]
        mgr = ResourceManager(specs, PreventionPolicy.ROLLBACK, Tracer(enabled=False))
        pool = self.create_pool(mgr)

        batches = [
            ActionBatch(
                "R1",
                0,
                (
                    Action("R1", 0, ActionType.ACQUIRE, "JOURNAL", 1, 0),
                    Action("R1", 0, ActionType.RELEASE, "JOURNAL", 1, 1),
                ),
            ),
            ActionBatch(
                "R2",
                0,
                (
                    Action("R2", 0, ActionType.ACQUIRE, "REFERENCE_BOOK", 1, 0),
                    Action("R2", 0, ActionType.RELEASE, "REFERENCE_BOOK", 1, 1),
                ),
            ),
        ]
        results = pool.run_batches(batches)
        pool.shutdown()

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].reader_id, "R1")
        self.assertEqual(results[0].done, 2)
        self.assertFalse(results[0].blocked)
        self.assertEqual(results[1].reader_id, "R2")
        self.assertEqual(results[1].done, 2)
        self.assertFalse(results[1].blocked)

    def test_batch_stops_at_first_blocked(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1)]
        mgr = ResourceManager(specs, PreventionPolicy.NONE, Tracer(enabled=False))
        pool = self.create_pool(mgr)

        # R1 acquires JOURNAL first
        mgr.acquire("R1", "JOURNAL", 0)

        # R2 batch tries to acquire JOURNAL, then do another action
        batches = [
            ActionBatch(
                "R2",
                1,
                (
                    Action("R2", 1, ActionType.ACQUIRE, "JOURNAL", 1, 0),
                    Action("R2", 1, ActionType.RELEASE, "JOURNAL", 1, 1),
                ),
            ),
        ]
        results = pool.run_batches(batches)
        pool.shutdown()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].reader_id, "R2")
        self.assertEqual(results[0].done, 0)
        self.assertTrue(results[0].blocked)

    def test_empty_batches(self) -> None:
        mgr = ResourceManager([], PreventionPolicy.NONE, Tracer(enabled=False))
        pool = self.create_pool(mgr)
        self.assertEqual(pool.run_batches([]), [])
        pool.shutdown()


class FakeWorkersContract(BaseWorkersContract):
    def create_pool(self, manager: ResourceManager) -> FakeWorkerPool:
        return FakeWorkerPool(manager, num_workers=2)


class RealWorkersConcurrency(unittest.TestCase):
    def test_real_threads_and_overlap(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1), ResourceSpec("REFERENCE_BOOK", 1)]
        mgr = ResourceManager(specs, PreventionPolicy.ROLLBACK, Tracer(enabled=False))
        with WorkerPool(mgr, num_workers=2) as pool:
            batches = [
                ActionBatch(
                    "R1",
                    0,
                    (Action("R1", 0, ActionType.ACQUIRE, "JOURNAL", 1, 0),),
                ),
                ActionBatch(
                    "R2",
                    0,
                    (Action("R2", 0, ActionType.ACQUIRE, "REFERENCE_BOOK", 1, 0),),
                ),
            ]
            results = pool.run_batches(batches)
            self.assertEqual(len(results), 2)
            # Verify results have thread names
            self.assertTrue(results[0].thread.startswith("worker-"))
            self.assertTrue(results[1].thread.startswith("worker-"))
            self.assertNotEqual(results[0].thread, results[1].thread)
            self.assertTrue(pool.recorded_overlaps)


if __name__ == "__main__":
    unittest.main()
