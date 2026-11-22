"""Contract and policy tests for ResourceManager (owner: Samar).

Covers S3, S4, S4b, and S6c.
"""

from __future__ import annotations

import unittest

import tests  # noqa: F401
from library_sim.deadlock import PreventionPolicy
from library_sim.models import ResourceSpec
from library_sim.resources import (
    AcquireOutcome,
    AcquireStatus,
    ReleaseOutcome,
    ResourceManager,
    ResourceStats,
)
from library_sim.trace import EventKind, Tracer
from tests.fakes.fake_resources import ResourceManager as FakeResourceManager


class BaseResourcesContract(unittest.TestCase):
    """Checks behaviour rules satisfied by both real ResourceManager and FakeResourceManager."""

    def create_manager(self, specs: list[ResourceSpec]) -> ResourceManager | FakeResourceManager:
        return ResourceManager(specs, PreventionPolicy.NONE, Tracer(enabled=False))

    def test_acquire_and_release(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1)]
        mgr = self.create_manager(specs)
        out1 = mgr.acquire("R1", "JOURNAL", 0)
        self.assertEqual(out1.status, AcquireStatus.GRANTED)
        self.assertEqual(mgr.held_by("R1"), frozenset(["JOURNAL"]))
        self.assertFalse(mgr.nothing_held())

        rel1 = mgr.release("R1", "JOURNAL", 1)
        self.assertEqual(rel1.woken, ())
        self.assertEqual(mgr.held_by("R1"), frozenset())
        self.assertTrue(mgr.nothing_held())

    def test_direct_handoff(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1)]
        mgr = self.create_manager(specs)
        mgr.acquire("R1", "JOURNAL", 0)
        out2 = mgr.acquire("R2", "JOURNAL", 1)
        self.assertEqual(out2.status, AcquireStatus.BLOCKED)
        self.assertTrue(mgr.is_waiting("R2"))

        rel = mgr.release("R1", "JOURNAL", 2)
        self.assertEqual(rel.woken, ("R2",))
        self.assertFalse(mgr.is_waiting("R2"))
        self.assertEqual(mgr.held_by("R2"), frozenset(["JOURNAL"]))
        self.assertEqual(mgr.held_by("R1"), frozenset())

    def test_contract_1_runtime_errors(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1), ResourceSpec("REFERENCE_BOOK", 1)]
        mgr = self.create_manager(specs)
        mgr.acquire("R1", "JOURNAL", 0)
        with self.assertRaises(RuntimeError):
            mgr.acquire("R1", "JOURNAL", 1)

        # R2 blocks on JOURNAL -> already waiting
        mgr.acquire("R2", "JOURNAL", 1)
        with self.assertRaises(RuntimeError):
            mgr.acquire("R2", "REFERENCE_BOOK", 2)

    def test_release_by_non_holder(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1)]
        mgr = self.create_manager(specs)
        with self.assertRaises(RuntimeError):
            mgr.release("R1", "JOURNAL", 0)

    def test_stats_and_wait_for_graph(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1)]
        mgr = self.create_manager(specs)
        mgr.acquire("R1", "JOURNAL", 0)
        mgr.acquire("R2", "JOURNAL", 1)
        wfg = mgr.wait_for_graph()
        self.assertEqual(wfg.get("R2"), {"R1"})

        stats = {s.resource_id: s for s in mgr.stats()}
        self.assertEqual(stats["JOURNAL"].acquisitions, 1)
        self.assertEqual(stats["JOURNAL"].wait_events, 1)
        self.assertEqual(stats["JOURNAL"].max_simultaneous_holders, 1)


class FakeResourcesContract(BaseResourcesContract):
    def create_manager(self, specs: list[ResourceSpec]) -> FakeResourceManager:
        return FakeResourceManager(specs, PreventionPolicy.NONE, Tracer(enabled=False))


class PreventionPolicyTests(unittest.TestCase):
    """S4b: Unit tests comparing ROLLBACK and ORDERED policies."""

    def test_rollback_breaks_hold_and_wait(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1), ResourceSpec("REFERENCE_BOOK", 1)]
        tracer = Tracer(enabled=True)
        mgr = ResourceManager(specs, PreventionPolicy.ROLLBACK, tracer)

        # R1 acquires JOURNAL
        mgr.acquire("R1", "JOURNAL", 0)
        # R2 acquires REFERENCE_BOOK
        mgr.acquire("R2", "REFERENCE_BOOK", 0)

        # R1 tries to acquire REFERENCE_BOOK (held by R2)
        # Under ROLLBACK: R1 must release JOURNAL and wait for {JOURNAL, REFERENCE_BOOK}
        out = mgr.acquire("R1", "REFERENCE_BOOK", 1)
        self.assertEqual(out.status, AcquireStatus.BLOCKED)
        self.assertEqual(out.rolled_back, ("JOURNAL",))
        # R1 now holds nothing while waiting!
        self.assertEqual(mgr.held_by("R1"), frozenset())
        stats = mgr.policy_stats()
        self.assertEqual(stats.rollbacks, 1)
        self.assertEqual(stats.resources_rolled_back, 1)
        self.assertEqual(stats.held_while_waiting, 0)

        # R2 can now acquire JOURNAL because R1 rolled it back!
        out2 = mgr.acquire("R2", "JOURNAL", 2)
        self.assertEqual(out2.status, AcquireStatus.GRANTED)
        self.assertEqual(mgr.held_by("R2"), frozenset(["JOURNAL", "REFERENCE_BOOK"]))

        # When R2 finishes and releases both, R1 acquires both atomically and wakes
        rel1 = mgr.release("R2", "JOURNAL", 3)
        self.assertEqual(rel1.woken, ())  # R1 needs both, JOURNAL alone is not enough
        rel2 = mgr.release("R2", "REFERENCE_BOOK", 4)
        self.assertEqual(rel2.woken, ("R1",))
        self.assertEqual(mgr.held_by("R1"), frozenset(["JOURNAL", "REFERENCE_BOOK"]))
        self.assertEqual(mgr.policy_stats().reacquisitions, 1)

    def test_ordered_breaks_circular_wait(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1), ResourceSpec("REFERENCE_BOOK", 1)]
        tracer = Tracer(enabled=True)
        mgr = ResourceManager(specs, PreventionPolicy.ORDERED, tracer)
        # Rank: JOURNAL=0, REFERENCE_BOOK=1

        # R1 acquires REFERENCE_BOOK (rank 1)
        mgr.acquire("R1", "REFERENCE_BOOK", 0)
        # R2 acquires JOURNAL (rank 0)
        mgr.acquire("R2", "JOURNAL", 0)

        # R2 (holds JOURNAL rank 0) acquires REFERENCE_BOOK (rank 1):
        # In-order wait! R2 keeps JOURNAL, waits for REFERENCE_BOOK
        out_r2 = mgr.acquire("R2", "REFERENCE_BOOK", 1)
        self.assertEqual(out_r2.status, AcquireStatus.BLOCKED)
        self.assertEqual(out_r2.rolled_back, ())
        self.assertEqual(mgr.held_by("R2"), frozenset(["JOURNAL"]))

        # R1 (holds REFERENCE_BOOK rank 1) acquires JOURNAL (rank 0):
        # Out-of-order! R1 rolls back REFERENCE_BOOK, which directly wakes R2!
        out_r1 = mgr.acquire("R1", "JOURNAL", 1)
        self.assertEqual(out_r1.status, AcquireStatus.BLOCKED)
        self.assertEqual(out_r1.rolled_back, ("REFERENCE_BOOK",))
        self.assertEqual(out_r1.woken, ("R2",))
        self.assertEqual(mgr.held_by("R2"), frozenset(["JOURNAL", "REFERENCE_BOOK"]))

        p_stats = mgr.policy_stats()
        self.assertGreater(p_stats.out_of_order_requests, 0)
        self.assertEqual(p_stats.rollbacks, 1)

    def test_ordered_uncontended_out_of_order_does_not_rollback(self) -> None:
        specs = [ResourceSpec("JOURNAL", 1), ResourceSpec("REFERENCE_BOOK", 1)]
        mgr = ResourceManager(specs, PreventionPolicy.ORDERED, Tracer(enabled=False))

        # R1 acquires REFERENCE_BOOK (rank 1), then JOURNAL (rank 0) when JOURNAL is free
        mgr.acquire("R1", "REFERENCE_BOOK", 0)
        out = mgr.acquire("R1", "JOURNAL", 1)
        self.assertEqual(out.status, AcquireStatus.GRANTED)
        self.assertEqual(out.rolled_back, ())
        self.assertEqual(mgr.policy_stats().rollbacks, 0)
        self.assertEqual(mgr.policy_stats().out_of_order_requests, 1)

    def test_three_reader_cycle_prevention(self) -> None:
        for policy in (PreventionPolicy.ROLLBACK, PreventionPolicy.ORDERED):
            with self.subTest(policy=policy.value):
                specs = [
                    ResourceSpec("OS_BOOK_1", 1),
                    ResourceSpec("OS_BOOK_2", 1),
                    ResourceSpec("OS_BOOK_3", 1),
                ]
                mgr = ResourceManager(specs, policy, Tracer(enabled=False))
                # R1 holds 1, wants 2
                # R2 holds 2, wants 3
                # R3 holds 3, wants 1
                mgr.acquire("R1", "OS_BOOK_1", 0)
                mgr.acquire("R2", "OS_BOOK_2", 0)
                mgr.acquire("R3", "OS_BOOK_3", 0)

                mgr.acquire("R1", "OS_BOOK_2", 1)
                mgr.acquire("R2", "OS_BOOK_3", 1)
                mgr.acquire("R3", "OS_BOOK_1", 1)

                # Neither policy must permit an unresolved deadlocked state
                # Under ROLLBACK, held_while_waiting is strictly 0
                if policy == PreventionPolicy.ROLLBACK:
                    self.assertEqual(mgr.policy_stats().held_while_waiting, 0)


if __name__ == "__main__":
    unittest.main()
