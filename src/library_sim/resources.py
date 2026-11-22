"""Thread-safe resource manager supporting mutual exclusion and deadlock prevention.

This module is the only shared mutable state accessed by concurrent worker
threads. All operations are synchronized via an internal lock.
"""

from __future__ import annotations

import threading
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import Enum

from .deadlock import PolicyStats, PreventionPolicy, resource_rank
from .models import ResourceSpec
from .trace import EventKind, Tracer


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


@dataclass
class _OrderedWaiter:
    reader_id: str
    sequence: list[str]
    reacquisition_targets: set[str]


class ResourceManager:
    """Thread-safe resource manager implementing NONE, ROLLBACK, and ORDERED policies."""

    def __init__(
        self,
        resources: Iterable[ResourceSpec],
        policy: PreventionPolicy,
        tracer: Tracer,
    ) -> None:
        self._policy = policy
        self._tracer = tracer
        self._lock = threading.Lock()

        self._resources: dict[str, ResourceSpec] = {r.id: r for r in resources}
        self._declared_ids: tuple[str, ...] = tuple(sorted(self._resources.keys()))

        # Ownership state
        self._holders: dict[str, str | None] = {r_id: None for r_id in self._declared_ids}
        self._held_by_reader: dict[str, set[str]] = {}

        # Usage statistics
        self._max_holders: dict[str, int] = {r_id: 0 for r_id in self._declared_ids}
        self._acquisitions: dict[str, int] = {r_id: 0 for r_id in self._declared_ids}
        self._wait_events: dict[str, int] = {r_id: 0 for r_id in self._declared_ids}
        self._exclusivity_violations = 0

        # Policy counters
        self._rollbacks = 0
        self._resources_rolled_back = 0
        self._reacquisitions = 0
        self._out_of_order_requests = 0
        self._held_while_waiting = 0

        # Wait queues
        # NONE policy: resource_id -> list of waiting reader_ids
        self._none_waiters: dict[str, list[str]] = {r_id: [] for r_id in self._declared_ids}
        # ROLLBACK policy: list of (reader_id, needed_set, rolled_back_set)
        self._rollback_waiters: list[tuple[str, frozenset[str], set[str]]] = []
        # ORDERED policy: resource_id -> list of _OrderedWaiter waiting on resource_id
        self._ordered_waiters: dict[str, list[_OrderedWaiter]] = {
            r_id: [] for r_id in self._declared_ids
        }
        self._waiting_readers: set[str] = set()

    def _rank(self, resource_id: str) -> int:
        return resource_rank(resource_id, self._declared_ids)

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
            all_free = all(h is None for h in self._holders.values())
            no_waiters = len(self._waiting_readers) == 0
            no_reader_holds = all(len(s) == 0 for s in self._held_by_reader.values())
            return all_free and no_waiters and no_reader_holds

    def stats(self) -> tuple[ResourceStats, ...]:
        with self._lock:
            return tuple(
                ResourceStats(
                    resource_id=r_id,
                    capacity=self._resources[r_id].capacity,
                    max_simultaneous_holders=self._max_holders[r_id],
                    acquisitions=self._acquisitions[r_id],
                    wait_events=self._wait_events[r_id],
                )
                for r_id in self._declared_ids
            )

    def policy_stats(self) -> PolicyStats:
        with self._lock:
            return PolicyStats(
                policy=self._policy,
                rollbacks=self._rollbacks,
                resources_rolled_back=self._resources_rolled_back,
                reacquisitions=self._reacquisitions,
                out_of_order_requests=self._out_of_order_requests,
                held_while_waiting=self._held_while_waiting,
            )

    def wait_for_graph(self) -> dict[str, set[str]]:
        with self._lock:
            graph: dict[str, set[str]] = {}
            if self._policy == PreventionPolicy.NONE:
                for r_id, waiters in self._none_waiters.items():
                    holder = self._holders[r_id]
                    if holder is not None:
                        for w in waiters:
                            graph.setdefault(w, set()).add(holder)
            elif self._policy == PreventionPolicy.ROLLBACK:
                for w, needed, _ in self._rollback_waiters:
                    for r_id in needed:
                        holder = self._holders.get(r_id)
                        if holder is not None and holder != w:
                            graph.setdefault(w, set()).add(holder)
            elif self._policy == PreventionPolicy.ORDERED:
                for r_id, waiters in self._ordered_waiters.items():
                    holder = self._holders[r_id]
                    if holder is not None:
                        for w in waiters:
                            if holder != w.reader_id:
                                graph.setdefault(w.reader_id, set()).add(holder)
            return graph

    def acquire(self, reader_id: str, resource_id: str, t: int) -> AcquireOutcome:
        with self._lock:
            if resource_id not in self._resources:
                raise ValueError(f"unknown resource {resource_id!r}")
            held = self._held_by_reader.get(reader_id, set())
            if resource_id in held:
                raise RuntimeError(
                    f"reader {reader_id} already holds resource {resource_id} [CONTRACT 1]"
                )
            if reader_id in self._waiting_readers:
                raise RuntimeError(
                    f"reader {reader_id} is already waiting [CONTRACT 1]"
                )

            if self._policy == PreventionPolicy.NONE:
                return self._acquire_none(reader_id, resource_id, t)
            elif self._policy == PreventionPolicy.ROLLBACK:
                return self._acquire_rollback(reader_id, resource_id, t)
            elif self._policy == PreventionPolicy.ORDERED:
                return self._acquire_ordered(reader_id, resource_id, t)
            else:
                raise ValueError(f"unsupported policy {self._policy}")

    def release(self, reader_id: str, resource_id: str, t: int) -> ReleaseOutcome:
        with self._lock:
            if resource_id not in self._resources:
                raise ValueError(f"unknown resource {resource_id!r}")
            current_holder = self._holders.get(resource_id)
            if current_holder != reader_id:
                self._exclusivity_violations += 1
                raise RuntimeError(
                    f"reader {reader_id} does not hold {resource_id} (held by {current_holder})"
                )

            if self._policy == PreventionPolicy.NONE:
                return self._release_none(reader_id, resource_id, t)
            elif self._policy == PreventionPolicy.ROLLBACK:
                return self._release_rollback(reader_id, resource_id, t)
            elif self._policy == PreventionPolicy.ORDERED:
                return self._release_ordered(reader_id, resource_id, t)
            else:
                raise ValueError(f"unsupported policy {self._policy}")

    # -------------------------------------------------------------------------
    # NONE Policy
    # -------------------------------------------------------------------------
    def _acquire_none(self, reader_id: str, resource_id: str, t: int) -> AcquireOutcome:
        current_holder = self._holders[resource_id]
        if current_holder is None:
            self._holders[resource_id] = reader_id
            self._held_by_reader.setdefault(reader_id, set()).add(resource_id)
            self._acquisitions[resource_id] += 1
            self._max_holders[resource_id] = max(self._max_holders[resource_id], 1)
            self._tracer.emit(t, EventKind.ACQUIRE, reader_id, resource_id)
            return AcquireOutcome(AcquireStatus.GRANTED, resource_id)

        self._wait_events[resource_id] += 1
        if len(self._held_by_reader.get(reader_id, set())) > 0:
            self._held_while_waiting += 1
        self._none_waiters[resource_id].append(reader_id)
        self._waiting_readers.add(reader_id)
        self._tracer.emit(
            t, EventKind.BLOCK, reader_id, resource_id, detail=f"held by {current_holder}"
        )
        return AcquireOutcome(AcquireStatus.BLOCKED, resource_id)

    def _release_none(self, reader_id: str, resource_id: str, t: int) -> ReleaseOutcome:
        self._held_by_reader[reader_id].remove(resource_id)
        self._tracer.emit(t, EventKind.RELEASE, reader_id, resource_id)

        if self._none_waiters[resource_id]:
            next_reader = self._none_waiters[resource_id].pop(0)
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

    # -------------------------------------------------------------------------
    # ROLLBACK Policy
    # -------------------------------------------------------------------------
    def _acquire_rollback(self, reader_id: str, resource_id: str, t: int) -> AcquireOutcome:
        current_holder = self._holders[resource_id]
        if current_holder is None:
            self._holders[resource_id] = reader_id
            self._held_by_reader.setdefault(reader_id, set()).add(resource_id)
            self._acquisitions[resource_id] += 1
            self._max_holders[resource_id] = max(self._max_holders[resource_id], 1)
            self._tracer.emit(t, EventKind.ACQUIRE, reader_id, resource_id)
            return AcquireOutcome(AcquireStatus.GRANTED, resource_id)

        self._wait_events[resource_id] += 1
        self._tracer.emit(
            t, EventKind.BLOCK, reader_id, resource_id, detail=f"held by {current_holder}"
        )

        held_resources = sorted(self._held_by_reader.get(reader_id, set()))
        if not held_resources:
            self._rollback_waiters.append((reader_id, frozenset([resource_id]), set()))
            self._waiting_readers.add(reader_id)
            return AcquireOutcome(AcquireStatus.BLOCKED, resource_id)

        # Reader holds H while blocking on resource_id -> Roll back ALL of H!
        self._rollbacks += 1
        self._resources_rolled_back += len(held_resources)
        for h in held_resources:
            self._held_by_reader[reader_id].remove(h)
            self._holders[h] = None
            self._tracer.emit(t, EventKind.ROLLBACK, reader_id, h)

        needed = frozenset(held_resources + [resource_id])
        rolled_back_set = set(held_resources)
        self._rollback_waiters.append((reader_id, needed, rolled_back_set))
        self._waiting_readers.add(reader_id)

        woken = self._process_rollback_waiters(t, just_freed_by=reader_id)
        return AcquireOutcome(
            AcquireStatus.BLOCKED,
            resource_id,
            rolled_back=tuple(held_resources),
            woken=tuple(woken),
        )

    def _release_rollback(self, reader_id: str, resource_id: str, t: int) -> ReleaseOutcome:
        self._held_by_reader[reader_id].remove(resource_id)
        self._holders[resource_id] = None
        self._tracer.emit(t, EventKind.RELEASE, reader_id, resource_id)

        woken = self._process_rollback_waiters(t, just_freed_by=reader_id)
        return ReleaseOutcome(resource_id, woken=tuple(woken))

    def _process_rollback_waiters(self, t: int, just_freed_by: str) -> list[str]:
        woken: list[str] = []
        changed = True
        while changed:
            changed = False
            for idx, (waiter_id, needed, rolled_back_set) in enumerate(self._rollback_waiters):
                if all(self._holders[res] is None for res in needed):
                    self._rollback_waiters.pop(idx)
                    self._waiting_readers.remove(waiter_id)
                    for res in sorted(needed):
                        self._holders[res] = waiter_id
                        self._held_by_reader.setdefault(waiter_id, set()).add(res)
                        self._acquisitions[res] += 1
                        self._max_holders[res] = max(self._max_holders[res], 1)
                        if res in rolled_back_set:
                            self._reacquisitions += 1
                        self._tracer.emit(
                            t,
                            EventKind.HANDOFF,
                            waiter_id,
                            res,
                            detail=f"from {just_freed_by}",
                        )
                    woken.append(waiter_id)
                    changed = True
                    break
        return woken

    # -------------------------------------------------------------------------
    # ORDERED Policy
    # -------------------------------------------------------------------------
    def _acquire_ordered(self, reader_id: str, resource_id: str, t: int) -> AcquireOutcome:
        held = self._held_by_reader.get(reader_id, set())
        rank_x = self._rank(resource_id)
        if any(self._rank(h) > rank_x for h in held):
            self._out_of_order_requests += 1

        current_holder = self._holders[resource_id]
        if current_holder is None and not self._ordered_waiters[resource_id]:
            self._holders[resource_id] = reader_id
            self._held_by_reader.setdefault(reader_id, set()).add(resource_id)
            self._acquisitions[resource_id] += 1
            self._max_holders[resource_id] = max(self._max_holders[resource_id], 1)
            self._tracer.emit(t, EventKind.ACQUIRE, reader_id, resource_id)
            return AcquireOutcome(AcquireStatus.GRANTED, resource_id)

        self._wait_events[resource_id] += 1
        self._tracer.emit(
            t, EventKind.BLOCK, reader_id, resource_id, detail=f"held by {current_holder}"
        )

        h_above = [h for h in held if self._rank(h) > rank_x]
        if not h_above:
            if len(held) > 0:
                self._held_while_waiting += 1
            waiter = _OrderedWaiter(
                reader_id=reader_id,
                sequence=[resource_id],
                reacquisition_targets=set(),
            )
            self._ordered_waiters[resource_id].append(waiter)
            self._waiting_readers.add(reader_id)
            return AcquireOutcome(AcquireStatus.BLOCKED, resource_id)

        # Out-of-order wait: roll back held resources ranked above X
        h_above_sorted = sorted(h_above, key=self._rank)
        self._rollbacks += 1
        self._resources_rolled_back += len(h_above_sorted)
        for h in h_above_sorted:
            self._held_by_reader[reader_id].remove(h)
            self._holders[h] = None
            self._tracer.emit(t, EventKind.ROLLBACK, reader_id, h)

        h_below = [h for h in held if self._rank(h) < rank_x]
        if len(h_below) > 0:
            self._held_while_waiting += 1

        sequence = [resource_id] + h_above_sorted
        waiter = _OrderedWaiter(
            reader_id=reader_id,
            sequence=sequence,
            reacquisition_targets=set(h_above_sorted),
        )
        self._ordered_waiters[resource_id].append(waiter)
        self._waiting_readers.add(reader_id)

        # Check if the rolled-back items can wake waiting readers
        woken: list[str] = []
        for h in h_above_sorted:
            woken.extend(self._handoff_ordered(h, t, just_freed_by=reader_id))

        return AcquireOutcome(
            AcquireStatus.BLOCKED,
            resource_id,
            rolled_back=tuple(h_above_sorted),
            woken=tuple(woken),
        )

    def _release_ordered(self, reader_id: str, resource_id: str, t: int) -> ReleaseOutcome:
        self._held_by_reader[reader_id].remove(resource_id)
        self._holders[resource_id] = None
        self._tracer.emit(t, EventKind.RELEASE, reader_id, resource_id)

        woken = self._handoff_ordered(resource_id, t, just_freed_by=reader_id)
        return ReleaseOutcome(resource_id, woken=tuple(woken))

    def _handoff_ordered(self, resource_id: str, t: int, just_freed_by: str) -> list[str]:
        woken: list[str] = []
        if not self._ordered_waiters[resource_id]:
            return woken

        waiter = self._ordered_waiters[resource_id].pop(0)
        # Grant resource_id to waiter
        self._holders[resource_id] = waiter.reader_id
        self._held_by_reader.setdefault(waiter.reader_id, set()).add(resource_id)
        self._acquisitions[resource_id] += 1
        self._max_holders[resource_id] = max(self._max_holders[resource_id], 1)
        if resource_id in waiter.reacquisition_targets:
            self._reacquisitions += 1
        self._tracer.emit(
            t, EventKind.HANDOFF, waiter.reader_id, resource_id, detail=f"from {just_freed_by}"
        )

        assert waiter.sequence[0] == resource_id
        waiter.sequence = waiter.sequence[1:]

        # Continue advancing waiter along its sequence
        while waiter.sequence:
            next_res = waiter.sequence[0]
            if self._holders[next_res] is None and not self._ordered_waiters[next_res]:
                self._holders[next_res] = waiter.reader_id
                self._held_by_reader.setdefault(waiter.reader_id, set()).add(next_res)
                self._acquisitions[next_res] += 1
                self._max_holders[next_res] = max(self._max_holders[next_res], 1)
                if next_res in waiter.reacquisition_targets:
                    self._reacquisitions += 1
                self._tracer.emit(t, EventKind.ACQUIRE, waiter.reader_id, next_res)
                waiter.sequence = waiter.sequence[1:]
            else:
                self._ordered_waiters[next_res].append(waiter)
                self._held_while_waiting += 1
                break

        if not waiter.sequence:
            self._waiting_readers.remove(waiter.reader_id)
            woken.append(waiter.reader_id)

        return woken
