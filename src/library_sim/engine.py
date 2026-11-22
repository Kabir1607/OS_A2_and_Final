"""Virtual-clock simulation coordinator for A2 and the Final project.

The engine coordinates the memory and Final collaborators; it does not
reimplement their allocation or synchronization policies.  The coordinator
owns all ``Reader`` and memory state, while Final worker threads receive only
resource action batches.
"""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import TYPE_CHECKING, Literal

from .models import Allocator, Reader, ReaderResult, Scheduler, SimulationInput, State

if TYPE_CHECKING:  # Final-only imports remain lazy at runtime.
    from .deadlock import PreventionPolicy
    from .trace import Tracer


@dataclass(frozen=True)
class CheckStats:
    """Safety counters emitted by Final output."""

    exclusivity_violations: int
    unresolved_deadlocks: int
    completed_count: int


@dataclass(frozen=True)
class SimulationResult:
    """Raw timestamps plus pool, resource, trace, and completion diagnostics."""

    readers: tuple[ReaderResult, ...]
    incomplete: tuple[str, ...]
    pool: object
    resources: tuple[object, ...]
    checks: CheckStats | None
    deadlock_cycles: tuple[tuple[str, ...], ...]
    trace: tuple[object, ...]
    policy_stats: object | None
    wall_time_s: float


class Simulation:
    """Run one deterministic virtual-clock simulation.

    A timestamp is drained in the frozen order: completions, arrivals,
    admission, dispatch, and any newly enabled zero-offset work.  The
    occupancy tracker is sampled only after that drain, so it records the
    state that persists until the next timestamp.
    """

    def __init__(
        self,
        inp: SimulationInput,
        scheduler: Scheduler,
        allocator: Allocator,
        *,
        mode: Literal["A2", "FINAL"],
        policy: PreventionPolicy | None = None,
        tracer: Tracer | None = None,
        pool_capacity: int = 6,
        num_librarians: int = 2,
        num_workers: int = 2,
    ) -> None:
        if mode not in ("A2", "FINAL"):
            raise ValueError(f"mode must be 'A2' or 'FINAL', got {mode!r}")
        if num_librarians < 1 or num_workers < 1:
            raise ValueError("librarian and worker counts must be positive")

        # Importing memory here keeps package inspection and Final-only
        # packaging independent from the unimplemented collaborator.
        from .memory import AdmissionQueue, OccupancyTracker, SeatPool

        self.inp = inp
        self.scheduler = scheduler
        self.allocator = allocator
        self.mode = mode
        self.policy = policy
        self.tracer = tracer
        self.pool = SeatPool(allocator, pool_capacity)
        self.admissions = AdmissionQueue(self.pool)
        self.occupancy = OccupancyTracker(pool_capacity)
        self.num_librarians = num_librarians
        self.num_workers = num_workers
        self.readers = {
            spec.id: Reader(spec, actions=inp.actions_for(spec.id))
            for spec in inp.readers
        }

    def _emit(self, t: int, kind: str, reader_id: str,
              resource_id: str | None = None, detail: str = "") -> None:
        """Emit an event only when a Final tracer was supplied."""
        if self.tracer is None:
            return
        from .trace import EventKind

        self.tracer.emit(t, EventKind(kind), reader_id, resource_id, detail)

    def _arrive(self, t: int) -> None:
        """Enqueue all readers arriving at ``t`` in string-ID order."""
        for reader in sorted(
            (r for r in self.readers.values() if r.spec.arrival == t),
            key=lambda r: r.id,
        ):
            reader.transition(State.BLOCKED_MEMORY)
            self.admissions.enqueue(reader.spec)
            self._emit(t, "ARRIVE", reader.id)
            self._emit(t, "BLOCK_MEMORY", reader.id)

    def _admit(self, t: int) -> bool:
        """Admit the FIFO prefix and place admitted readers in ReadyQueue."""
        admitted = self.admissions.admit_ready()
        for reader_id, start in admitted:
            reader = self.readers[reader_id]
            reader.mem_admit = t
            reader.seat_start = start
            reader.transition(State.READY)
            self.ready.push(reader.spec)
            self._emit(
                t,
                "ADMIT",
                reader.id,
                detail=f"seats={start}-{start + reader.spec.space_req - 1}",
            )
        return bool(admitted)

    def _dispatch_a2(self, t: int) -> bool:
        """Fill idle librarians with complete A2 service bursts."""
        changed = False
        for librarian in range(self.num_librarians):
            if librarian in self.running or not self.ready:
                continue
            spec = self.ready.pop()
            reader = self.readers[spec.id]
            reader.transition(State.RUNNING)
            reader.librarian = librarian
            reader.dispatched_at = t
            reader.executed_at_dispatch = reader.executed
            reader.start = t if reader.start is None else reader.start
            self.running[librarian] = reader
            self._emit(t, "DISPATCH", reader.id, detail=f"librarian={librarian}")
            changed = True
        return changed

    def _result_for(self, reader: Reader) -> ReaderResult:
        """Build the immutable result consumed by Kabir's metrics module."""
        if reader.mem_admit is None or reader.start is None or reader.completion is None:
            raise AssertionError(f"missing timestamp for {reader.id}")
        return ReaderResult(
            reader.id,
            reader.spec.arrival,
            reader.spec.priority,
            reader.spec.service,
            reader.start,
            reader.completion,
            reader.mem_admit,
            reader.resource_wait,
        )

    def _finish(self, end_time: int, cycles: list[tuple[str, ...]]) -> SimulationResult:
        """Finalize collaborators and preserve incomplete-reader information."""
        resources: tuple[object, ...] = ()
        checks: CheckStats | None = None
        policy_stats: object | None = None
        trace: tuple[object, ...] = ()
        if self.manager is not None:
            self.worker_pool.shutdown()
            resources = tuple(self.manager.stats())
            policy_stats = self.manager.policy_stats()
            trace = tuple(self.tracer.events())
            from .trace import audit_exclusivity

            checks = CheckStats(
                max(
                    self.manager.exclusivity_violations(),
                    audit_exclusivity(trace, self.inp.resources),
                ),
                len(cycles),
                len(self.completed),
            )
        elif self.mode == "FINAL":
            # A resource-free Final run is the A2 baseline, but Final output
            # still requires its three CHECK lines.
            checks = CheckStats(0, len(cycles), len(self.completed))

        pool = self.occupancy.finish(end_time)
        return SimulationResult(
            tuple(self._result_for(self.readers[key]) for key in sorted(self.completed)),
            tuple(sorted(
                key for key, reader in self.readers.items()
                if reader.state is not State.TERMINATED
            )),
            pool,
            resources,
            checks,
            tuple(cycles),
            trace,
            policy_stats,
            perf_counter() - self.started_at,
        )

    def _run_a2(self) -> SimulationResult:
        """Execute the A2 event loop using integer virtual time only."""
        arrivals = sorted(reader.spec.arrival for reader in self.readers.values())
        arrival_index = 0
        now = arrivals[0]
        cycles: list[tuple[str, ...]] = []

        while len(self.completed) < len(self.readers):
            while True:
                changed = False

                # Completions precede arrivals, sorted by reader ID.
                for librarian, reader in sorted(
                    tuple(self.running.items()), key=lambda pair: pair[1].id
                ):
                    if reader.dispatched_at is None:
                        continue
                    if now < reader.dispatched_at + reader.spec.service:
                        continue
                    reader.executed = reader.spec.service
                    reader.completion = now
                    reader.transition(State.TERMINATED)
                    self.pool.release(reader.id)
                    del self.running[librarian]
                    self.completed.add(reader.id)
                    self._emit(now, "COMPLETE", reader.id)
                    changed = True

                if arrival_index < len(arrivals) and arrivals[arrival_index] == now:
                    same_time = 0
                    while (arrival_index + same_time < len(arrivals)
                           and arrivals[arrival_index + same_time] == now):
                        same_time += 1
                    self._arrive(now)
                    arrival_index += same_time
                    changed = True
                changed |= self._admit(now)
                changed |= self._dispatch_a2(now)
                if not changed:
                    break

            # One sample per processed timestamp, after all state changes.
            self.occupancy.sample(now, self.pool)
            if len(self.completed) == len(self.readers):
                break

            future = arrivals[arrival_index:] + [
                reader.dispatched_at + reader.spec.service
                for reader in self.running.values()
                if reader.dispatched_at is not None
            ]
            if not future:
                # Never spin forever if a collaborator violates its contract.
                cycles.append(tuple(sorted(
                    key for key, reader in self.readers.items()
                    if reader.state is not State.TERMINATED
                )))
                break
            now = min(future)

        return self._finish(now, cycles)

    def _prepare_final(self) -> None:
        """Construct Samar's collaborators only for resource-bearing Final runs."""
        from .deadlock import DEFAULT_POLICY
        from .resources import ResourceManager
        from .trace import Tracer
        from .workers import WorkerPool

        if self.tracer is None:
            self.tracer = Tracer(enabled=False)
        self.manager = ResourceManager(
            self.inp.resources, self.policy or DEFAULT_POLICY, self.tracer
        )
        self.worker_pool = WorkerPool(self.manager, self.num_workers)

    def _final_action_round(self, now: int) -> bool:
        """Run all action batches due at ``now`` and apply results in two phases."""
        from .workers import ActionBatch

        batches = []
        due_readers: list[Reader] = []
        for reader in sorted(self.running.values(), key=lambda item: item.id):
            assert reader.dispatched_at is not None
            reader.executed = min(
                reader.spec.service,
                reader.executed_at_dispatch + now - reader.dispatched_at,
            )
            if reader.next_action >= len(reader.actions):
                continue
            if reader.actions[reader.next_action].work_offset != reader.executed:
                continue
            offset = reader.actions[reader.next_action].work_offset
            end = reader.next_action
            while end < len(reader.actions) and reader.actions[end].work_offset == offset:
                end += 1
            due_readers.append(reader)
            batches.append(ActionBatch(
                reader.id,
                now,
                reader.actions[reader.next_action:end],
            ))
        if not batches:
            return False

        results = self.worker_pool.run_batches(batches)
        woken: set[str] = set()
        # Apply every blocked/done result before processing any wake-up.
        for reader, result in zip(due_readers, results):
            reader.next_action += result.done
            woken.update(result.woken)
            if not result.blocked:
                continue
            reader.transition(State.BLOCKED_RESOURCE)
            reader.blocked_since = now
            if reader.librarian is not None:
                del self.running[reader.librarian]
            reader.librarian = None
            reader.dispatched_at = None

        for reader_id in sorted(woken):
            reader = self.readers[reader_id]
            if reader.state is not State.BLOCKED_RESOURCE:
                raise AssertionError(f"woken reader {reader_id} is not blocked")
            reader.transition(State.READY)
            if reader.blocked_since is not None:
                reader.resource_wait += now - reader.blocked_since
            reader.blocked_since = None
            # The manager handed over the blocked ACQUIRE already.  Advancing
            # here prevents the engine from attempting a double acquire.
            reader.next_action += 1
            self.ready.push(reader.spec)
            self._emit(now, "UNBLOCK", reader.id)
        return True

    def _run_final(self) -> SimulationResult:
        """Run resource actions, worker batches, and virtual-time wake-ups."""
        arrivals = sorted(reader.spec.arrival for reader in self.readers.values())
        arrival_index = 0
        now = arrivals[0]
        cycles: list[tuple[str, ...]] = []

        while len(self.completed) < len(self.readers):
            while True:
                changed = False
                changed |= self._final_action_round(now)

                # Completions happen after actions at this timestamp, allowing
                # RELEASE at offset SERVICE to be observed first.
                for librarian, reader in sorted(
                    tuple(self.running.items()), key=lambda pair: pair[1].id
                ):
                    if reader.dispatched_at is None:
                        continue
                    if reader.executed < reader.spec.service:
                        continue
                    if reader.next_action < len(reader.actions):
                        continue
                    reader.completion = now
                    reader.transition(State.TERMINATED)
                    self.pool.release(reader.id)
                    del self.running[librarian]
                    self.completed.add(reader.id)
                    self._emit(now, "COMPLETE", reader.id)
                    changed = True

                if arrival_index < len(arrivals) and arrivals[arrival_index] == now:
                    same_time = 0
                    while (arrival_index + same_time < len(arrivals)
                           and arrivals[arrival_index + same_time] == now):
                        same_time += 1
                    self._arrive(now)
                    arrival_index += same_time
                    changed = True
                changed |= self._admit(now)
                changed |= self._dispatch_a2(now)
                if not changed:
                    break

            self.occupancy.sample(now, self.pool)
            if len(self.completed) == len(self.readers):
                break

            future = arrivals[arrival_index:]
            for reader in self.running.values():
                if reader.dispatched_at is None:
                    continue
                future.append(reader.dispatched_at + reader.spec.service - reader.executed_at_dispatch)
                if reader.next_action < len(reader.actions):
                    future.append(
                        reader.dispatched_at
                        + reader.actions[reader.next_action].work_offset
                        - reader.executed_at_dispatch
                    )
            if not future:
                from .deadlock import find_cycles

                found = find_cycles(self.manager.wait_for_graph())
                cycles.extend(tuple(sorted(cycle)) for cycle in found)
                for cycle in found:
                    self._emit(now, "DEADLOCK", min(cycle), detail="->".join((*cycle, cycle[0])))
                break
            now = min(t for t in future if t >= now)

        return self._finish(now, cycles)

    def run(self) -> SimulationResult:
        """Run A2, or the resource-free Final baseline."""
        self.started_at = perf_counter()
        self.running: dict[int, Reader] = {}
        self.completed: set[str] = set()
        self.ready = None
        self.manager = None
        self.worker_pool = None
        from .scheduler import ReadyQueue

        self.ready = ReadyQueue(self.scheduler)
        if self.mode == "FINAL" and (self.inp.resources or self.inp.actions):
            self._prepare_final()
            return self._run_final()
        return self._run_a2()


def simulate(
    inp: SimulationInput,
    scheduler: Scheduler,
    allocator: Allocator,
    mode: Literal["A2", "FINAL"],
    **kwargs: object,
) -> SimulationResult:
    """Convenience function matching the public contract."""
    return Simulation(inp, scheduler, allocator, mode=mode, **kwargs).run()
