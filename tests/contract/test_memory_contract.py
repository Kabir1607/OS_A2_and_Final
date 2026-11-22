"""Aarush A5: hand-calculated checks for the library seating rules.

Run from the repository root with:
    python3 -m unittest tests.contract.test_memory_contract -v
"""

from __future__ import annotations

import dataclasses
import unittest

import tests  # noqa: F401 (makes the shared src package importable)
from library_sim import memory as real_memory
from tests.fakes import fake_memory
from library_sim.models import Allocator, ReaderSpec, Scheduler, SimulationInput, State


def reader(reader_id: str, seats: int) -> ReaderSpec:
    """Make a reader request; service scheduling is irrelevant to queue unit tests."""
    return ReaderSpec(reader_id, 0, 1, 1, "REGULAR", seats)


class MemoryContract(unittest.TestCase):
    memory = real_memory


class AllocationFunctions(MemoryContract):
    """A1: choose adjacent seats without modifying the room."""

    def test_free_run_boundaries(self) -> None:
        cases = [
            ([], []),
            ([None] * 6, [(0, 6)]),
            (["R1"] * 6, []),
            ([None, "R1", None, None, "R2", None], [(0, 1), (2, 2), (5, 1)]),
        ]
        for slots, expected in cases:
            with self.subTest(slots=slots):
                before = slots.copy()
                self.assertEqual(self.memory.free_runs(slots), expected)
                self.assertEqual(slots, before)
                self.assertEqual(self.memory.free_runs(tuple(slots)), expected)

    def test_spec_example(self) -> None:
        runs = self.memory.free_runs(["X", "X", None, None, "X", None])
        expected = {Allocator.FIRST_FIT: 2, Allocator.BEST_FIT: 5, Allocator.WORST_FIT: 2}
        for allocator, start in expected.items():
            with self.subTest(allocator=allocator):
                self.assertEqual(self.memory.choose_run(runs, 1, allocator), start)

    def test_all_three_can_choose_different_runs(self) -> None:
        # Configurable test rooms allow a simple three-way comparison.
        runs = [(0, 3), (4, 2), (7, 4)]
        expected = {Allocator.FIRST_FIT: 0, Allocator.BEST_FIT: 4, Allocator.WORST_FIT: 7}
        for allocator, start in expected.items():
            self.assertEqual(self.memory.choose_run(runs, 2, allocator), start)

    def test_equal_holes_choose_lowest_start_without_mutation(self) -> None:
        runs = [(4, 2), (0, 2)]
        for allocator in Allocator:
            self.assertEqual(self.memory.choose_run(runs, 1, allocator), 0)
            self.assertEqual(runs, [(4, 2), (0, 2)])

    def test_exact_fit_full_capacity_and_no_fit(self) -> None:
        for allocator in Allocator:
            self.assertEqual(self.memory.choose_run([(0, 6)], 6, allocator), 0)
            self.assertEqual(self.memory.choose_run([(0, 1), (2, 2)], 2, allocator), 2)
            self.assertIsNone(self.memory.choose_run([(0, 2), (3, 2)], 3, allocator))
            self.assertIsNone(self.memory.choose_run([], 1, allocator))

    def test_invalid_arguments(self) -> None:
        for k in (0, -1):
            with self.assertRaises(ValueError):
                self.memory.choose_run([(0, 6)], k, Allocator.FIRST_FIT)
        with self.assertRaises(ValueError):
            self.memory.choose_run([(0, 6)], 1, "UNKNOWN")  # type: ignore[arg-type]


class SeatReservations(MemoryContract):
    """A2: reserve and release exactly the seats recorded for each reader."""

    def test_empty_room(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        self.assertEqual(pool.capacity, 6)
        self.assertIs(pool.allocator, Allocator.FIRST_FIT)
        self.assertEqual(pool.snapshot(), (None,) * 6)
        self.assertEqual(pool.free_runs(), [(0, 6)])
        self.assertEqual((pool.occupied, pool.largest_free_run, pool.external_fragmentation()),
                         (0, 6, 0))

    def test_full_room_then_reuse(self) -> None:
        for allocator in Allocator:
            with self.subTest(allocator=allocator):
                pool = self.memory.SeatPool(allocator)
                self.assertEqual(pool.allocate("R1", 6), 0)
                self.assertEqual(pool.snapshot(), ("R1",) * 6)
                self.assertEqual((pool.occupied, pool.largest_free_run), (6, 0))
                self.assertEqual(pool.external_fragmentation(), 0)
                self.assertIsNone(pool.allocate("R2", 1))
                self.assertEqual(pool.release("R1"), (0, 6))
                self.assertEqual(pool.allocate("R1", 1), 0)

    def test_reservations_follow_selected_allocator(self) -> None:
        expected = {Allocator.FIRST_FIT: 0, Allocator.BEST_FIT: 5, Allocator.WORST_FIT: 0}
        for allocator, start in expected.items():
            pool = self.memory.SeatPool(allocator)
            pool.allocate("R1", 2)
            pool.allocate("R2", 3)
            pool.release("R1")  # Two free seats before R2; one free seat after it.
            self.assertEqual(pool.allocate("R3", 1), start)
            self.assertEqual(pool.snapshot()[2:5], ("R2",) * 3)

    def test_failed_fragmented_request_preserves_register(self) -> None:
        for allocator in Allocator:
            pool = self.memory.SeatPool(allocator)
            pool.allocate("R1", 2)
            pool.allocate("R2", 2)
            pool.allocate("R3", 2)
            pool.release("R1")
            pool.release("R3")  # Four free seats, but only two are adjacent.
            before = pool.snapshot()
            self.assertEqual(pool.external_fragmentation(), 2)
            self.assertIsNone(pool.allocate("R4", 3))
            self.assertEqual(pool.snapshot(), before)
            # A failed request must not create a reservation entry either.
            with self.assertRaises(KeyError):
                pool.release("R4")
            self.assertEqual(pool.allocate("R4", 2), 0)

    def test_release_is_exact_and_coalesces_both_neighbors(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        pool.allocate("R1", 2)
        pool.allocate("R2", 2)
        pool.allocate("R3", 2)
        self.assertEqual(pool.release("R1"), (0, 2))
        self.assertEqual(pool.snapshot(), (None, None, "R2", "R2", "R3", "R3"))
        pool.release("R3")
        self.assertEqual(pool.free_runs(), [(0, 2), (4, 2)])
        self.assertEqual(pool.release("R2"), (2, 2))
        self.assertEqual(pool.free_runs(), [(0, 6)])
        self.assertEqual(pool.external_fragmentation(), 0)

    def test_invalid_reservations_leave_seats_unchanged(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        pool.allocate("R1", 2)
        before = pool.snapshot()
        for k in (0, -1, 7):
            with self.assertRaises(ValueError):
                pool.allocate("R2", k)
        with self.assertRaises(ValueError):
            pool.allocate("R1", 1)
        with self.assertRaises(KeyError):
            pool.release("missing")
        self.assertEqual(pool.snapshot(), before)
        pool.release("R1")
        with self.assertRaises(KeyError):
            pool.release("R1")

    def test_capacity_and_snapshot_independence(self) -> None:
        for capacity in (0, -2):
            with self.assertRaises(ValueError):
                self.memory.SeatPool(Allocator.FIRST_FIT, capacity)
        with self.assertRaises(ValueError):
            self.memory.SeatPool("UNKNOWN")  # type: ignore[arg-type]
        pool = self.memory.SeatPool(Allocator.FIRST_FIT, capacity=9)
        original = pool.snapshot()
        pool.allocate("R1", 9)
        self.assertIsInstance(original, tuple)
        self.assertEqual(original, (None,) * 9)
        self.assertEqual(pool.occupied, 9)
        pool.release("R1")
        self.assertEqual(pool.snapshot(), original)


class AdmissionLine(MemoryContract):
    """A3: a reader cannot jump ahead of a larger blocked request."""

    def test_empty_queue_and_enqueue_order(self) -> None:
        queue = self.memory.AdmissionQueue(self.memory.SeatPool(Allocator.FIRST_FIT))
        self.assertIsNone(queue.head)
        self.assertEqual(len(queue), 0)
        self.assertEqual(queue.admit_ready(), [])
        queue.enqueue(reader("R2", 1))
        queue.enqueue(reader("R10", 1))
        # Sorting is the engine's job, not the admission queue's.
        self.assertEqual(queue.waiting_ids(), ["R2", "R10"])
        self.assertEqual(queue.head, "R2")
        copied_ids = queue.waiting_ids()
        copied_ids.clear()
        self.assertEqual(len(queue), 2)

    def test_head_blocks_smaller_reader_then_both_are_admitted(self) -> None:
        for allocator in Allocator:
            pool = self.memory.SeatPool(allocator)
            queue = self.memory.AdmissionQueue(pool)
            for reader_id, seats in [("R1", 4), ("R2", 3), ("R3", 1)]:
                queue.enqueue(reader(reader_id, seats))
            self.assertEqual(queue.admit_ready(), [("R1", 0)])
            self.assertEqual(queue.waiting_ids(), ["R2", "R3"])
            self.assertEqual(queue.head, "R2")
            before = pool.snapshot()
            self.assertEqual(queue.admit_ready(), [])
            self.assertEqual(pool.snapshot(), before)
            pool.release("R1")
            self.assertEqual(queue.admit_ready(), [("R2", 0), ("R3", 3)])
            self.assertEqual(queue.waiting_ids(), [])
            self.assertIsNone(queue.head)

    def test_admits_only_fitting_prefix_and_preserves_every_other_reader(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        queue = self.memory.AdmissionQueue(pool)
        for reader_id, seats in [("R1", 2), ("R2", 4), ("R3", 1), ("R4", 1)]:
            queue.enqueue(reader(reader_id, seats))
        self.assertEqual(queue.admit_ready(), [("R1", 0), ("R2", 2)])
        self.assertEqual(queue.waiting_ids(), ["R3", "R4"])
        pool.release("R1")
        self.assertEqual(queue.admit_ready(), [("R3", 0), ("R4", 1)])
        self.assertEqual(len(queue), 0)


class OccupancyStatistics(MemoryContract):
    """A4: hand-calculated seat-time, peaks, and fragmentation reports."""

    def test_weighted_integral_nonzero_start_and_idle_tail(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        tracker = self.memory.OccupancyTracker(6)
        pool.allocate("R1", 2)
        tracker.sample(5, pool)
        pool.allocate("R2", 2)
        tracker.sample(8, pool)
        pool.release("R1")
        pool.release("R2")
        tracker.sample(10, pool)
        # 2 seats * 3 time units + 4 * 2 + 0 * 2 = 14 seat-time units.
        stats = tracker.finish(12)
        self.assertEqual(stats, self.memory.PoolStats("SPACE", 6, 4, 14, 0, 5, 12))
        self.assertAlmostEqual(stats.utilization_pct, 14 / 42 * 100)

    def test_finish_includes_last_interval_without_double_counting(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        tracker = self.memory.OccupancyTracker(6)
        pool.allocate("R1", 3)
        tracker.sample(2, pool)
        self.assertEqual(tracker.finish(6).occupied_integral, 12)
        self.assertEqual(tracker.finish(6).occupied_integral, 12)
        self.assertEqual(tracker.finish(8).occupied_integral, 18)
        # A report did not advance the underlying observation log.
        pool.release("R1")
        tracker.sample(4, pool)
        self.assertEqual(tracker.finish(8).occupied_integral, 6)

    def test_equal_timestamps_add_no_time_and_update_observation(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        tracker = self.memory.OccupancyTracker(6)
        pool.allocate("R1", 2)
        tracker.sample(3, pool)
        pool.allocate("R2", 2)
        tracker.sample(3, pool)
        self.assertEqual(tracker.finish(5).occupied_integral, 8)
        self.assertEqual(tracker.finish(5).peak_occupied, 4)

    def test_fragmentation_peak_survives_later_empty_room(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        tracker = self.memory.OccupancyTracker(6)
        pool.allocate("R1", 2)
        pool.allocate("R2", 2)
        tracker.sample(0, pool)
        pool.release("R1")
        tracker.sample(2, pool)  # . . R2 R2 . . : free 4, largest 2, fragmentation 2.
        pool.release("R2")
        tracker.sample(5, pool)
        self.assertEqual(tracker.finish(5), self.memory.PoolStats("SPACE", 6, 4, 14, 2, 0, 5))

    def test_only_sampled_states_contribute_to_peaks(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        tracker = self.memory.OccupancyTracker(6)
        pool.allocate("R1", 6)
        pool.release("R1")  # Engine microsteps before its end-of-timestamp sample.
        tracker.sample(0, pool)
        self.assertEqual(tracker.finish(1).peak_occupied, 0)

    def test_zero_duration_and_unsampled_reports(self) -> None:
        tracker = self.memory.OccupancyTracker(6)
        self.assertEqual(tracker.finish(7), self.memory.PoolStats("SPACE", 6, 0, 0, 0, 7, 7))
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        pool.allocate("R1", 6)
        tracker.sample(10, pool)
        stats = tracker.finish(10)
        self.assertEqual((stats.peak_occupied, stats.occupied_integral), (6, 0))
        self.assertEqual(stats.utilization_pct, 0.0)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            stats.capacity = 8  # type: ignore[misc]

    def test_full_utilization_and_initial_idle_interval(self) -> None:
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        tracker = self.memory.OccupancyTracker(6)
        tracker.sample(5, pool)
        pool.allocate("R1", 6)
        tracker.sample(7, pool)
        self.assertEqual(tracker.finish(9).utilization_pct, 50.0)
        full_tracker = self.memory.OccupancyTracker(6)
        full_tracker.sample(7, pool)
        self.assertEqual(full_tracker.finish(9).utilization_pct, 100.0)

    def test_invalid_observations_do_not_change_tracker(self) -> None:
        for capacity in (0, -1):
            with self.assertRaises(ValueError):
                self.memory.OccupancyTracker(capacity)
        tracker = self.memory.OccupancyTracker(6)
        with self.assertRaises(ValueError):
            tracker.sample(0, self.memory.SeatPool(Allocator.FIRST_FIT, 3))
        pool = self.memory.SeatPool(Allocator.FIRST_FIT)
        pool.allocate("R1", 2)
        tracker.sample(5, pool)
        before = tracker.finish(9)
        with self.assertRaises(ValueError):
            tracker.sample(4, pool)
        with self.assertRaises(ValueError):
            tracker.sample(6, self.memory.SeatPool(Allocator.FIRST_FIT, 3))
        with self.assertRaises(ValueError):
            tracker.finish(4)
        self.assertEqual(tracker.finish(9), before)


class MemoryWithExistingEngine(MemoryContract):
    """Check the new module's connection to the existing coordinator."""

    def test_fifo_timestamps_conservation_and_resource_free_final(self) -> None:
        from library_sim.engine import Simulation, simulate

        inp = SimulationInput(2, (
            ReaderSpec("R1", 0, 1, 4, "REGULAR", 4),
            ReaderSpec("R2", 0, 1, 2, "REGULAR", 3),
            ReaderSpec("R3", 0, 1, 1, "REGULAR", 1),
        ))
        for scheduler in Scheduler:
            for allocator in Allocator:
                with self.subTest(scheduler=scheduler, allocator=allocator):
                    simulation = Simulation(inp, scheduler, allocator, mode="A2")
                    result = simulation.run()
                    self.assertEqual(
                        [(r.id, r.mem_admit, r.start, r.completion) for r in result.readers],
                        [("R1", 0, 0, 4), ("R2", 4, 4, 6), ("R3", 4, 4, 5)],
                    )
                    self.assertEqual(result.pool, self.memory.PoolStats("SPACE", 6, 4, 23, 0, 0, 6))
                    self.assertEqual(result.incomplete, ())
                    self.assertEqual(simulation.pool.snapshot(), (None,) * 6)
                    self.assertTrue(all(r.state is State.TERMINATED
                                        for r in simulation.readers.values()))
                    final = simulate(inp, scheduler, allocator, "FINAL")
                    self.assertEqual(final.readers, result.readers)
                    self.assertEqual(final.pool, result.pool)
                    self.assertEqual(final.resources, ())
                    self.assertEqual(final.checks.completed_count, 3)
                    self.assertEqual(final.checks.exclusivity_violations, 0)
                    self.assertEqual(final.checks.unresolved_deadlocks, 0)


# Both modules must satisfy exactly the same seating behavior checks.

class FakeAllocationFunctions(AllocationFunctions):
    memory = fake_memory


class FakeSeatReservations(SeatReservations):
    memory = fake_memory


class FakeAdmissionLine(AdmissionLine):
    memory = fake_memory


class FakeOccupancyStatistics(OccupancyStatistics):
    memory = fake_memory


if __name__ == "__main__":
    unittest.main()
