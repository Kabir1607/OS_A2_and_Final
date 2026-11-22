"""Independent small seating stand-in for A7c; no real-memory dependency.

Keep this intentionally direct: a list is the seating register, a list is
also the admission line, and samples are retained for later accounting.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from library_sim.models import Allocator, ReaderSpec

FreeRun = tuple[int, int]


def free_runs(slots: Sequence[str | None]) -> list[FreeRun]:
    """Find each maximal empty group in the seating register."""
    result = []
    index = 0
    while index < len(slots):
        if slots[index] is not None:
            index += 1
            continue
        start = index
        while index < len(slots) and slots[index] is None:
            index += 1
        result.append((start, index-start))
    return result


def choose_run(runs: Sequence[FreeRun], k: int, allocator: Allocator) -> int | None:
    """Recommend a group; equal sizes always prefer the earlier seat."""
    if k < 1 or allocator not in tuple(Allocator):
        raise ValueError('invalid request or allocator')
    fitting = [run for run in runs if run[1] >= k]
    if not fitting:
        return None
    if allocator == Allocator.FIRST_FIT:
        return min(fitting)[0]
    if allocator == Allocator.BEST_FIT:
        return min(fitting, key=lambda run:(run[1],run[0]))[0]
    return min(fitting, key=lambda run:(-run[1],run[0]))[0]


class SeatPool:
    """Reserve adjacent seats without maintaining a separate reservation map."""
    def __init__(self, allocator: Allocator, capacity: int = 6) -> None:
        if capacity < 1 or allocator not in tuple(Allocator):
            raise ValueError('invalid capacity or allocator')
        self.capacity, self.allocator = capacity, allocator
        self._slots: list[str | None] = [None]*capacity

    def allocate(self, reader_id: str, k: int) -> int | None:
        """Seat the reader, or leave the entire register unchanged."""
        if reader_id in self._slots or not 1 <= k <= self.capacity:
            raise ValueError('duplicate reservation or invalid request')
        start = choose_run(self.free_runs(), k, self.allocator)
        if start is not None:
            self._slots[start:start+k] = [reader_id]*k
        return start

    def release(self, reader_id: str) -> FreeRun:
        """Return this reader's exact seats and report the original block."""
        indices = [i for i, owner in enumerate(self._slots) if owner == reader_id]
        if not indices:
            raise KeyError(reader_id)
        for i in indices:
            self._slots[i] = None
        return (indices[0],len(indices))

    def free_runs(self) -> list[FreeRun]:
        return free_runs(self._slots)

    @property
    def occupied(self) -> int:
        return self.capacity-self._slots.count(None)

    @property
    def largest_free_run(self) -> int:
        return max((length for start,length in self.free_runs()),default=0)

    def external_fragmentation(self) -> int:
        return self.capacity-self.occupied-self.largest_free_run

    def snapshot(self) -> tuple[str | None, ...]:
        return tuple(self._slots)


class AdmissionQueue:
    """Seat readers strictly in enqueue order, never skipping a blocked head."""
    def __init__(self, pool: SeatPool) -> None:
        self._pool, self._line = pool, []

    def enqueue(self, spec: ReaderSpec) -> None:
        self._line.append(spec)

    def admit_ready(self) -> list[tuple[str, int]]:
        admitted = []
        while self._line:
            request = self._line[0]
            start = self._pool.allocate(request.id,request.space_req)
            if start is None:
                break
            admitted.append((request.id,start))
            self._line.pop(0)
        return admitted

    @property
    def head(self) -> str | None:
        return self._line[0].id if self._line else None

    def waiting_ids(self) -> list[str]:
        return [r.id for r in self._line]

    def __len__(self) -> int:
        return len(self._line)


@dataclass(frozen=True)
class PoolStats:
    """Immutable seat-time report with the same public fields as the contract."""
    name: str
    capacity: int
    peak_occupied: int
    occupied_integral: int
    max_ext_frag: int
    start_time: int
    end_time: int

    @property
    def utilization_pct(self) -> float:
        elapsed = self.end_time-self.start_time
        return self.occupied_integral/(self.capacity*elapsed)*100 if elapsed else 0.0


class OccupancyTracker:
    """Retain seating observations and calculate intervals when asked to finish."""
    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError('capacity must be positive')
        self._capacity = capacity
        self._samples: list[tuple[int,int,int]] = []

    def sample(self, t: int, pool: SeatPool) -> None:
        if pool.capacity != self._capacity or (self._samples and t < self._samples[-1][0]):
            raise ValueError('invalid observation')
        self._samples.append((t,pool.occupied,pool.external_fragmentation()))

    def finish(self, end_time: int) -> PoolStats:
        if not self._samples:
            return PoolStats('SPACE',self._capacity,0,0,0,end_time,end_time)
        if end_time < self._samples[-1][0]:
            raise ValueError('end precedes last sample')
        integral = 0
        for i,(t,occupied,frag) in enumerate(self._samples):
            next_time = self._samples[i+1][0] if i+1 < len(self._samples) else end_time
            integral += occupied*(next_time-t)
        return PoolStats('SPACE',self._capacity,max(s[1] for s in self._samples),
                         integral,max(s[2] for s in self._samples),self._samples[0][0],end_time)
