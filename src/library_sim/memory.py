"""Aarush A1-A4: the library's seating register, waiting line, and statistics.

A seat contains its reader's ID, or None when free. Readers reserve adjacent
seats before joining the librarian's ready queue and keep them until completion.
Only the engine coordinator uses this module, so no thread locks are needed.
Public interfaces follow the memory section of ``library_sim.pyi``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .models import Allocator, ReaderSpec

# A maximal group of adjacent free seats: (first seat index, number of seats).
FreeRun = tuple[int, int]


def free_runs(slots: Sequence[str | None]) -> list[FreeRun]:
    """Inspect the seating register and return free groups in seat-index order.

    For example, ["R1", None, None] gives [(1, 2)]. The input is unchanged.
    An empty register or a fully occupied room gives an empty list.
    """
    runs: list[FreeRun] = []
    start: int | None = None
    for index, owner in enumerate(slots):
        if owner is None:
            if start is None:
                start = index
        elif start is not None:
            runs.append((start, index - start))
            start = None

    # A free group can extend all the way to the last seat.
    if start is not None:
        runs.append((start, len(slots) - start))
    return runs


def choose_run(runs: Sequence[FreeRun], k: int, allocator: Allocator) -> int | None:
    """Choose where a k-seat reader would sit, without reserving any seats.

    First Fit scans from the lowest seat index; Best/Worst Fit choose the
    smallest/largest suitable group. Equal sizes keep the lowest index.
    Return None if none fits; raise ValueError for k < 1 or an unknown policy.
    ``runs`` must describe valid free groups, as returned by free_runs().
    """
    if k < 1:
        raise ValueError("seat request must be positive")
    if allocator not in (Allocator.FIRST_FIT, Allocator.BEST_FIT, Allocator.WORST_FIT):
        raise ValueError(f"unknown allocator: {allocator!r}")

    chosen: FreeRun | None = None
    # Sorting a copy also makes First Fit correct if the caller's list is unsorted.
    for start, length in sorted(runs):
        if length < k:
            continue
        if allocator == Allocator.FIRST_FIT:
            return start
        if chosen is None:
            chosen = (start, length)
        elif allocator == Allocator.BEST_FIT and length < chosen[1]:
            chosen = (start, length)
        elif allocator == Allocator.WORST_FIT and length > chosen[1]:
            chosen = (start, length)
    return None if chosen is None else chosen[0]


class SeatPool:
    """The seating register and reservation record for one reading room."""

    capacity: int
    allocator: Allocator

    def __init__(self, allocator: Allocator, capacity: int = 6) -> None:
        """Open an empty room using allocator and capacity seats (normally six).

        Raise ValueError for a nonpositive capacity or an unknown allocator.
        A different capacity is useful for tests, not standard graded runs.
        """
        if capacity < 1:
            raise ValueError("seat capacity must be positive")
        if allocator not in (Allocator.FIRST_FIT, Allocator.BEST_FIT, Allocator.WORST_FIT):
            raise ValueError(f"unknown allocator: {allocator!r}")
        self.capacity = capacity
        self.allocator = allocator
        self._slots: list[str | None] = [None] * capacity
        self._allocations: dict[str, FreeRun] = {}

    def allocate(self, reader_id: str, k: int) -> int | None:
        """Reserve k adjacent seats for reader_id; return their first index.

        Return None without changes if no group fits. Raise ValueError if the
        reader already has a reservation or k is outside 1..capacity.
        """
        if reader_id in self._allocations:
            raise ValueError(f"reader {reader_id} already holds seats")
        if not 1 <= k <= self.capacity:
            raise ValueError(f"seat request must be between 1 and {self.capacity}")

        start = choose_run(self.free_runs(), k, self.allocator)
        if start is None:
            return None

        # Commit only after finding a complete adjacent group: no partial seating.
        for index in range(start, start + k):
            self._slots[index] = reader_id
        self._allocations[reader_id] = (start, k)
        return start

    def release(self, reader_id: str) -> FreeRun:
        """Clear this reader's reservation and return its (start, length).

        Raise KeyError if the reader holds no seats. Newly adjacent free seats
        automatically appear as one group in the next free_runs() scan.
        """
        start, length = self._allocations.pop(reader_id)
        for index in range(start, start + length):
            self._slots[index] = None
        return (start, length)

    def free_runs(self) -> list[FreeRun]:
        """Return the room's maximal adjacent free groups in seat-index order."""
        return free_runs(self._slots)

    @property
    def occupied(self) -> int:
        """Count reserved seats, including readers waiting for a librarian."""
        return sum(owner is not None for owner in self._slots)

    @property
    def largest_free_run(self) -> int:
        """Return the largest adjacent free group size, or zero for a full room."""
        largest = 0
        for start, length in self.free_runs():
            largest = max(largest, length)
        return largest

    def external_fragmentation(self) -> int:
        """Measure scattered space: total free seats minus the largest free group.

        Both a completely free room and a full room have fragmentation zero.
        """
        total_free = self.capacity - self.occupied
        return total_free - self.largest_free_run

    def snapshot(self) -> tuple[str | None, ...]:
        """Return an immutable seating picture; later reservations cannot change it."""
        return tuple(self._slots)


class AdmissionQueue:
    """The strict FIFO line for seats, separate from the librarian ready queue."""

    def __init__(self, pool: SeatPool) -> None:
        """Create an empty waiting line attached to the supplied reading room."""
        self._pool = pool
        self._waiting: list[ReaderSpec] = []

    def enqueue(self, spec: ReaderSpec) -> None:
        """Append a reader's request; the engine supplies arrival/ID order.

        Reader IDs and request sizes are already validated by the input parser.
        This method does not reserve seats or alter the reader's lifecycle.
        """
        self._waiting.append(spec)

    def admit_ready(self) -> list[tuple[str, int]]:
        """Seat the fitting FIFO prefix and return (reader ID, first seat) pairs.

        Stop at the first reader who cannot fit, even if a later request would
        fit. Allocation errors propagate; unsuccessful requests stay queued.
        The engine sets admission times and makes admitted readers READY.
        """
        admitted: list[tuple[str, int]] = []
        while self._waiting:
            spec = self._waiting[0]
            start = self._pool.allocate(spec.id, spec.space_req)
            if start is None:
                break  # Head-of-line blocking: never look past this reader.
            self._waiting.pop(0)
            admitted.append((spec.id, start))
        return admitted

    @property
    def head(self) -> str | None:
        """Return the first waiting reader's ID, or None for an empty line."""
        return self._waiting[0].id if self._waiting else None

    def waiting_ids(self) -> list[str]:
        """Return a separate list of waiting IDs in FIFO order."""
        return [spec.id for spec in self._waiting]

    def __len__(self) -> int:
        """Count readers still waiting for seats, not readers already seated."""
        return len(self._waiting)


@dataclass(frozen=True)
class PoolStats:
    """Immutable room-usage report, constructed from the seven recorded fields.

    occupied_integral is seat-time, not a count of readers. The observation
    window begins with the first arrival and ends with the last completion
    in a successful engine run. name is "SPACE" for the Library.
    """

    name: str
    capacity: int
    peak_occupied: int
    occupied_integral: int
    max_ext_frag: int
    start_time: int
    end_time: int

    @property
    def utilization_pct(self) -> float:
        """Return used seat-time / available seat-time as a percentage.

        A zero-duration report has zero utilization, avoiding division by zero.
        """
        elapsed = self.end_time - self.start_time
        if elapsed == 0:
            return 0.0
        return self.occupied_integral / (self.capacity * elapsed) * 100.0


class OccupancyTracker:
    """A room-usage log: each seating observation lasts until the next one."""

    def __init__(self, capacity: int) -> None:
        """Start an unsampled log for a room; reject nonpositive capacity."""
        if capacity < 1:
            raise ValueError("seat capacity must be positive")
        self._capacity = capacity
        self._start_time: int | None = None
        self._last_time: int | None = None
        self._last_occupied = 0
        self._occupied_integral = 0
        self._peak_occupied = 0
        self._max_ext_frag = 0

    def sample(self, t: int, pool: SeatPool) -> None:
        """Record seating after all engine events at virtual time t finish.

        Equal times are allowed and add no seat-time. Raise ValueError for a
        backward time or a pool with a different capacity, leaving the log
        unchanged. The engine calls this once per processed timestamp.
        """
        if pool.capacity != self._capacity:
            raise ValueError("sampled pool capacity does not match tracker capacity")
        if self._last_time is not None and t < self._last_time:
            raise ValueError("sample time must be non-decreasing")

        if self._last_time is None:
            self._start_time = t
        else:
            # Use PREVIOUS occupancy: today's seating did not occupy yesterday's seats.
            self._occupied_integral += self._last_occupied * (t - self._last_time)
        self._last_time = t
        self._last_occupied = pool.occupied
        self._peak_occupied = max(self._peak_occupied, self._last_occupied)
        self._max_ext_frag = max(self._max_ext_frag, pool.external_fragmentation())

    def finish(self, end_time: int) -> PoolStats:
        """Return a usage report through end_time without changing the log.

        Include the last observed occupancy up to end_time. Repeated calls do
        not double-count. Raise ValueError if end_time precedes the last sample.
        With no samples, return an empty report starting and ending at end_time.
        """
        if self._last_time is None:
            return PoolStats("SPACE", self._capacity, 0, 0, 0, end_time, end_time)
        if end_time < self._last_time:
            raise ValueError("end time must not precede the last sample")

        integral = self._occupied_integral
        integral += self._last_occupied * (end_time - self._last_time)
        assert self._start_time is not None
        return PoolStats(
            "SPACE", self._capacity, self._peak_occupied, integral,
            self._max_ext_frag, self._start_time, end_time,
        )
