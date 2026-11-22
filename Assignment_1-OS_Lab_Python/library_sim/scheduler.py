"""The A1 scheduling policies, reused unchanged by A2 and the Final.

IDs are compared as plain strings, so "R10" sorts before "R2", exactly as
the specification requires (and as std::string comparison did in C++).
"""

from __future__ import annotations

import heapq
from typing import Callable

from .models import ReaderSpec, Scheduler


def fcfs_key(spec: ReaderSpec) -> tuple[int, str]:
    """Earlier arrival first; equal arrivals by lexicographic ID."""
    return (spec.arrival, spec.id)


def priority_key(spec: ReaderSpec) -> tuple[int, int, str]:
    """Smaller priority number first, then earlier arrival, then lexicographic ID."""
    return (spec.priority, spec.arrival, spec.id)


def key_for(scheduler: Scheduler) -> Callable[[ReaderSpec], tuple[object, ...]]:
    if scheduler is Scheduler.FCFS:
        return fcfs_key
    if scheduler is Scheduler.PRIORITY:
        return priority_key
    raise ValueError(f"unknown scheduler: {scheduler!r}")


class ReadyQueue:
    """READY readers ordered by the scheduler's key (a binary heap).

    Not thread-safe: only the engine's coordinator thread uses it. Keys are
    unique because reader IDs are unique, so insertion order never matters.
    """

    def __init__(self, scheduler: Scheduler) -> None:
        self._key = key_for(scheduler)
        self._heap: list[tuple[tuple[object, ...], str, ReaderSpec]] = []
        self._ids: set[str] = set()

    def push(self, spec: ReaderSpec) -> None:
        if spec.id in self._ids:
            raise ValueError(f"reader {spec.id} is already in the ready queue")
        heapq.heappush(self._heap, (self._key(spec), spec.id, spec))
        self._ids.add(spec.id)

    def pop(self) -> ReaderSpec:
        if not self._heap:
            raise IndexError("pop from an empty ready queue")
        _, reader_id, spec = heapq.heappop(self._heap)
        self._ids.remove(reader_id)
        return spec

    def peek(self) -> ReaderSpec | None:
        return self._heap[0][2] if self._heap else None

    def __len__(self) -> int:
        return len(self._heap)

    def __bool__(self) -> bool:
        return bool(self._heap)

    def __contains__(self, reader_id: object) -> bool:
        return reader_id in self._ids
