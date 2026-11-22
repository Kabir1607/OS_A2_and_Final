"""Concurrency and stress tests for shared resources (task S7, owner: Samar).

Tests race conditions, mutual exclusion across multiple threads, direct handoffs,
and randomized workloads verifying zero exclusivity violations.
"""

from __future__ import annotations

import random
import threading
import unittest

import tests  # noqa: F401
from library_sim.deadlock import PreventionPolicy
from library_sim.models import Action, ActionType, ResourceSpec
from library_sim.resources import AcquireStatus, ResourceManager
from library_sim.trace import Tracer, audit_exclusivity
from library_sim.workers import ActionBatch, WorkerPool


class ConcurrencyStressTests(unittest.TestCase):
    def test_many_readers_competing_for_single_book(self) -> None:
        """Many readers race to acquire the same book. Holders must never exceed 1."""
        tracer = Tracer(enabled=True)
        specs = [ResourceSpec("REFERENCE_BOOK", 1)]
        mgr = ResourceManager(specs, PreventionPolicy.ROLLBACK, tracer)

        num_threads = 10
        barrier = threading.Barrier(num_threads)
        errors: list[Exception] = []

        def worker(rid: str) -> None:
            try:
                barrier.wait()
                out = mgr.acquire(rid, "REFERENCE_BOOK", 0)
                if out.status == AcquireStatus.GRANTED:
                    # Hold briefly then release
                    mgr.release(rid, "REFERENCE_BOOK", 1)
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=worker, args=(f"R{i}",), name=f"worker-{i}")
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])
        self.assertEqual(mgr.exclusivity_violations(), 0)
        self.assertEqual(audit_exclusivity(tracer.events(), specs), 0)

    def test_different_copies_held_in_parallel(self) -> None:
        """OS_BOOK_3 and OS_BOOK_7 held simultaneously by distinct readers."""
        tracer = Tracer(enabled=True)
        specs = [ResourceSpec("OS_BOOK_3", 1), ResourceSpec("OS_BOOK_7", 1)]
        mgr = ResourceManager(specs, PreventionPolicy.ORDERED, tracer)

        out1 = mgr.acquire("R1", "OS_BOOK_3", 0)
        out2 = mgr.acquire("R2", "OS_BOOK_7", 0)

        self.assertEqual(out1.status, AcquireStatus.GRANTED)
        self.assertEqual(out2.status, AcquireStatus.GRANTED)
        self.assertEqual(mgr.held_by("R1"), frozenset(["OS_BOOK_3"]))
        self.assertEqual(mgr.held_by("R2"), frozenset(["OS_BOOK_7"]))
        self.assertEqual(mgr.exclusivity_violations(), 0)

        mgr.release("R1", "OS_BOOK_3", 1)
        mgr.release("R2", "OS_BOOK_7", 1)
        self.assertTrue(mgr.nothing_held())

    def test_worker_pool_batch_concurrency(self) -> None:
        """Batches run across WorkerPool executing releases that wake waiting readers."""
        tracer = Tracer(enabled=True)
        specs = [ResourceSpec("JOURNAL", 1)]
        mgr = ResourceManager(specs, PreventionPolicy.ROLLBACK, tracer)

        with WorkerPool(mgr, num_workers=2) as pool:
            # Batch 1: R1 acquires JOURNAL
            # Batch 2: R2 tries to acquire JOURNAL (will block)
            batches_t0 = [
                ActionBatch(
                    "R1", 0, (Action("R1", 0, ActionType.ACQUIRE, "JOURNAL", 1, 0),)
                ),
            ]
            res_t0 = pool.run_batches(batches_t0)
            self.assertEqual(res_t0[0].done, 1)

            batches_t1 = [
                ActionBatch(
                    "R2", 1, (Action("R2", 1, ActionType.ACQUIRE, "JOURNAL", 1, 0),)
                ),
            ]
            res_t1 = pool.run_batches(batches_t1)
            self.assertTrue(res_t1[0].blocked)

            # Batch 3: R1 releases JOURNAL (should wake R2)
            batches_t2 = [
                ActionBatch(
                    "R1", 2, (Action("R1", 2, ActionType.RELEASE, "JOURNAL", 1, 0),)
                ),
            ]
            res_t2 = pool.run_batches(batches_t2)
            self.assertEqual(res_t2[0].woken, ("R2",))

            # R2 now holds JOURNAL; R2 releases it
            batches_t3 = [
                ActionBatch(
                    "R2", 3, (Action("R2", 3, ActionType.RELEASE, "JOURNAL", 1, 0),)
                ),
            ]
            res_t3 = pool.run_batches(batches_t3)
            self.assertEqual(res_t3[0].done, 1)

        self.assertTrue(mgr.nothing_held())
        self.assertEqual(mgr.exclusivity_violations(), 0)

    def test_randomized_workloads_invariants(self) -> None:
        """Randomized resource requests executed under ROLLBACK and ORDERED."""
        rng = random.Random(42)
        declared_names = [f"OS_BOOK_{i}" for i in range(1, 5)]
        specs = [ResourceSpec(name, 1) for name in declared_names]

        for policy in (PreventionPolicy.ROLLBACK, PreventionPolicy.ORDERED):
            tracer = Tracer(enabled=True)
            mgr = ResourceManager(specs, policy, tracer)

            for step in range(50):
                rid = f"R{rng.randint(1, 5)}"
                book = rng.choice(declared_names)
                held = mgr.held_by(rid)

                if book in held:
                    mgr.release(rid, book, step)
                elif not mgr.is_waiting(rid):
                    mgr.acquire(rid, book, step)

            self.assertEqual(mgr.exclusivity_violations(), 0)
            self.assertEqual(audit_exclusivity(tracer.events(), specs), 0)


if __name__ == "__main__":
    unittest.main()
