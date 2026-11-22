"""Shared fake for ResourceManager (S6c).

Provides a minimal stand-in matching library_sim.resources signatures and
behaviour (direct handoff, trace events under lock, wait-for graph).
"""

from __future__ import annotations

import threading
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum

from library_sim.deadlock import PolicyStats, PreventionPolicy, resource_rank
from library_sim.models import ResourceSpec
from library_sim.trace import EventKind, Tracer


class AcquireStatus(str, Enum):
    GRANTED = "GRANTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class AcquireOutcome:
    status: AcquireStatus
    resource_id: str
    rolled_back: tuple[str, ...] = ()
    woken: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReleaseOutcome:
    resource_id: str
    woken: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResourceStats:
    resource_id: str
    capacity: int
    max_simultaneous_holders: int
    acquisitions: int
    wait_events: int


class ResourceManager:
    """Minimal shared fake resource manager."""

    def __init__(
        self,
        resources: Iterable[ResourceSpec],
        policy: PreventionPolicy,
        tracer: Tracer,
    ) -> None:
        self._policy = policy
        self._tracer = tracer
        self._lock = threading.Lock()
        self._resources = {r.id: r for r in resources}
        self._declared_ids = tuple(sorted(self._resources.keys()))
        self._holders: dict[str, str | None] = {r_id: None for r_id in self._declared_ids}
        self._held_by_reader: dict[str, set[str]] = {}
        self._max_holders: dict[str, int] = {r_id: 0 for r_id in self._declared_ids}
        self._acquisitions: dict[str, int] = {r_id: 0 for r_id in self._declared_ids}
        self._wait_events: dict[str, int] = {r_id: 0 for r_id in self._declared_ids}
        self._exclusivity_violations = 0
        self._waiters: dict[str, list[str]] = {r_id: [] for r_id in self._declared_ids}
        self._waiting_readers: set[str] = set()

    def is_waiting(self, reader_id: str) -> bool:
        with self._lock:
            return reader_id in self._waiting_readers

    def held_by(self, reader_id: str) -> frozenset[str]:
        with self._lock:
            return frozenset(self._held_by_reader.get(reader_id, set()))

    def exclusivity_violations(self) -> int:
        with self._lock:
            return self._exclusivity_violations

    def nothing_held(self) -> bool:
        with self._lock:
            return all(h is None for h in self._holders.values()) and not self._waiting_readers

    def stats(self) -> tuple[ResourceStats, ...]:
        with self._lock:
            return tuple(
                ResourceStats(
                    r_id,
                    self._resources[r_id].capacity,
                    self._max_holders[r_id],
                    self._acquisitions[r_id],
                    self._wait_events[r_id],
                )
                for r_id in self._declared_ids
            )

    def policy_stats(self) -> PolicyStats:
        with self._lock:
            return PolicyStats(
                policy=self._policy,
                rollbacks=0,
                resources_rolled_back=0,
                reacquisitions=0,
                out_of_order_requests=0,
                held_while_waiting=0,
            )

    def wait_for_graph(self) -> dict[str, set[str]]:
        with self._lock:
            graph: dict[str, set[str]] = {}
            for r_id, waiters in self._waiters.items():
                holder = self._holders[r_id]
                if holder is not None:
                    for w in waiters:
                        graph.setdefault(w, set()).add(holder)
            return graph

    def acquire(self, reader_id: str, resource_id: str, t: int) -> AcquireOutcome:
        with self._lock:
            held = self._held_by_reader.get(reader_id, set())
            if resource_id in held:
                raise RuntimeError(f"reader {reader_id} already holds {resource_id}")
            if reader_id in self._waiting_readers:
                raise RuntimeError(f"reader {reader_id} is already waiting")

            current = self._holders[resource_id]
            if current is None:
                self._holders[resource_id] = reader_id
                self._held_by_reader.setdefault(reader_id, set()).add(resource_id)
                self._acquisitions[resource_id] += 1
                self._max_holders[resource_id] = max(self._max_holders[resource_id], 1)
                self._tracer.emit(t, EventKind.ACQUIRE, reader_id, resource_id)
                return AcquireOutcome(AcquireStatus.GRANTED, resource_id)

            self._wait_events[resource_id] += 1
            self._waiters[resource_id].append(reader_id)
            self._waiting_readers.add(reader_id)
            self._tracer.emit(
                t, EventKind.BLOCK, reader_id, resource_id, detail=f"held by {current}"
            )
            return AcquireOutcome(AcquireStatus.BLOCKED, resource_id)

    def release(self, reader_id: str, resource_id: str, t: int) -> ReleaseOutcome:
        with self._lock:
            if self._holders.get(resource_id) != reader_id:
                self._exclusivity_violations += 1
                raise RuntimeError(f"reader {reader_id} does not hold {resource_id}")

            self._held_by_reader[reader_id].remove(resource_id)
            self._tracer.emit(t, EventKind.RELEASE, reader_id, resource_id)

            if self._waiters[resource_id]:
                next_reader = self._waiters[resource_id].pop(0)
                self._waiting_readers.remove(next_reader)
                self._holders[resource_id] = next_reader
                self._held_by_reader.setdefault(next_reader, set()).add(resource_id)
                self._acquisitions[resource_id] += 1
                self._tracer.emit(
                    t, EventKind.HANDOFF, next_reader, resource_id, detail=f"from {reader_id}"
                )
                return ReleaseOutcome(resource_id, woken=(next_reader,))

            self._holders[resource_id] = None
            return ReleaseOutcome(resource_id, woken=())
