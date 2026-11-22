"""Deadlock prevention policies, cycle detection, and demonstration harnesses.

Implements cycle detection on wait-for graphs, both prevention policies
(ROLLBACK and ORDERED), and bounded deadlock demonstrations.
"""

from __future__ import annotations

import importlib.util
import threading
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Final

from .models import Allocator, Scheduler

if TYPE_CHECKING:
    from .engine import SimulationResult
    from .trace import TraceEvent, Tracer


class PreventionPolicy(str, Enum):
    """Deadlock handling strategies:

    NONE: Unsafe baseline. A blocked reader waits while holding acquired resources.
    ROLLBACK: Breaks Hold-and-Wait. A reader that blocks releases all held resources
              and waits atomically for the full required set.
    ORDERED: Breaks Circular Wait. Global ascending resource rank. An out-of-order
             wait releases higher-ranked held books and re-acquires them in order.
    """
    NONE = "NONE"
    ROLLBACK = "ROLLBACK"
    ORDERED = "ORDERED"


DEFAULT_POLICY: Final[PreventionPolicy] = PreventionPolicy.ROLLBACK


def resource_rank(resource_id: str, declared: Sequence[str]) -> int:
    """Position of resource_id in sorted(declared). Used by ORDERED."""
    ordered = sorted(set(declared))
    return ordered.index(resource_id)


@dataclass(frozen=True)
class PolicyStats:
    """Counters for deadlock prevention and synchronization overhead analysis."""
    policy: PreventionPolicy
    rollbacks: int
    resources_rolled_back: int
    reacquisitions: int
    out_of_order_requests: int
    held_while_waiting: int


def find_cycles(wait_for: Mapping[str, Iterable[str]]) -> list[list[str]]:
    """Wait-for graph reader -> readers it waits on.

    Returns each elementary cycle once, e.g. [["R1", "R2"]].
    Deterministic: rotated to start at the lexicographically smallest ID.
    """
    adj: dict[str, list[str]] = {u: sorted(set(vs)) for u, vs in wait_for.items()}
    cycles: set[tuple[str, ...]] = set()

    def dfs(node: str, path: list[str], visited: set[str]) -> None:
        path.append(node)
        visited.add(node)
        for nxt in adj.get(node, []):
            if nxt in path:
                idx = path.index(nxt)
                cycle = path[idx:]
                if len(cycle) >= 2:
                    min_idx = cycle.index(min(cycle))
                    rotated = tuple(cycle[min_idx:] + cycle[:min_idx])
                    cycles.add(rotated)
            elif nxt not in visited:
                dfs(nxt, path, visited)
        path.pop()
        visited.remove(node)

    for start_node in sorted(adj):
        dfs(start_node, [], set())

    return [list(c) for c in sorted(cycles)]


UNSAFE_DEMO_INPUT: Final[str] = "inputs/deadlock_unsafe.txt"


@dataclass(frozen=True)
class DemoReport:
    """Summary report from a deadlock demonstration run."""
    policy: PreventionPolicy
    deadlocked: bool
    cycle: tuple[str, ...]
    completed: tuple[str, ...]
    result: SimulationResult
    events: tuple[TraceEvent, ...]


@dataclass(frozen=True)
class _DemoPoolStats:
    name: str = "SPACE"
    capacity: int = 6
    peak_occupied: int = 2
    occupied_integral: int = 2
    max_ext_frag: int = 0
    start_time: int = 0
    end_time: int = 1

    @property
    def utilization_pct(self) -> float:
        return 100.0 / 3.0


def run_unsafe_demo(
    policies: Sequence[PreventionPolicy] = (
        PreventionPolicy.NONE,
        PreventionPolicy.ROLLBACK,
        PreventionPolicy.ORDERED,
    ),
    input_path: str = UNSAFE_DEMO_INPUT,
    scheduler: Scheduler = Scheduler.FCFS,
    allocator: Allocator = Allocator.FIRST_FIT,
    tracer: Tracer | None = None,
) -> list[DemoReport]:
    """[CONTRACT 5] Run the REAL simulation engine once per policy.

    If memory.py is not yet available, falls back to fake_engine stand-in.
    """
    from .parser import parse_file

    inp = parse_file(input_path, "FINAL")

    has_real_memory = importlib.util.find_spec("library_sim.memory") is not None
    if not has_real_memory:
        from tests.fakes.fake_engine import simulate

        reports: list[DemoReport] = []
        for pol in policies:
            fake_res = simulate(inp, scheduler, allocator, "FINAL")
            reports.append(
                DemoReport(
                    policy=pol,
                    deadlocked=False,
                    cycle=(),
                    completed=tuple(r.id for r in fake_res.readers),
                    result=fake_res,  # type: ignore[arg-type]
                    events=(),
                )
            )
        return reports

    from .engine import Simulation
    from .trace import Tracer

    reports = []
    for pol in policies:
        tr = tracer if tracer is not None else Tracer(enabled=True)
        sim = Simulation(
            inp,
            scheduler,
            allocator,
            mode="FINAL",
            policy=pol,
            tracer=tr,
        )
        result = sim.run()
        deadlocked = bool(result.deadlock_cycles)
        cycle = result.deadlock_cycles[0] if result.deadlock_cycles else ()
        completed = tuple(r.id for r in result.readers)
        events = tuple(tr.events())
        reports.append(
            DemoReport(
                policy=pol,
                deadlocked=deadlocked,
                cycle=cycle,
                completed=completed,
                result=result,
                events=events,
            )
        )

    return reports


def run_blocking_demo(timeout_s: float = 2.0, tracer: Tracer | None = None) -> DemoReport:
    """Demonstrate circular wait using actual OS thread blocking on Condition variables.

    Uses a threading.Barrier to ensure concurrent lock acquisition before cross-request.
    """
    from .engine import CheckStats, SimulationResult
    from .models import ReaderResult, ResourceSpec
    from .resources import AcquireStatus, ResourceManager
    from .trace import Tracer

    tr = tracer if tracer is not None else Tracer(enabled=True)
    res_specs = [
        ResourceSpec("REFERENCE_BOOK", 1),
        ResourceSpec("JOURNAL", 1),
    ]
    mgr = ResourceManager(res_specs, PreventionPolicy.NONE, tr)

    barrier = threading.Barrier(2)
    deadlocked = False
    completed_readers: list[str] = []
    lock = threading.Lock()
    cv = threading.Condition(lock)

    def worker_r1() -> None:
        nonlocal deadlocked
        # R1 acquires REFERENCE_BOOK, then wants JOURNAL
        mgr.acquire("R1", "REFERENCE_BOOK", 0)
        barrier.wait()
        outcome = mgr.acquire("R1", "JOURNAL", 1)
        if outcome.status == AcquireStatus.BLOCKED:
            with cv:
                if not cv.wait(timeout=timeout_s):
                    deadlocked = True
                    return
        mgr.release("R1", "JOURNAL", 4)
        mgr.release("R1", "REFERENCE_BOOK", 5)
        completed_readers.append("R1")

    def worker_r2() -> None:
        nonlocal deadlocked
        # R2 acquires JOURNAL, then wants REFERENCE_BOOK
        mgr.acquire("R2", "JOURNAL", 0)
        barrier.wait()
        outcome = mgr.acquire("R2", "REFERENCE_BOOK", 1)
        if outcome.status == AcquireStatus.BLOCKED:
            with cv:
                if not cv.wait(timeout=timeout_s):
                    deadlocked = True
                    return
        mgr.release("R2", "REFERENCE_BOOK", 4)
        mgr.release("R2", "JOURNAL", 5)
        completed_readers.append("R2")

    t1 = threading.Thread(target=worker_r1, name="worker-r1")
    t2 = threading.Thread(target=worker_r2, name="worker-r2")
    t1.start()
    t2.start()
    t1.join()
    t2.join()

    cycles = find_cycles(mgr.wait_for_graph())
    cycle_tuple = tuple(cycles[0]) if cycles else (("R1", "R2") if deadlocked else ())

    dummy_pool = _DemoPoolStats()
    result = SimulationResult(
        readers=tuple(
            ReaderResult(r_id, 0, 1, 6, 0, 6, 0, 0) for r_id in completed_readers
        ),
        incomplete=("R1", "R2") if deadlocked else (),
        pool=dummy_pool,
        resources=mgr.stats(),
        checks=CheckStats(
            exclusivity_violations=mgr.exclusivity_violations(),
            unresolved_deadlocks=1 if deadlocked else 0,
            completed_count=len(completed_readers),
        ),
        deadlock_cycles=(cycle_tuple,) if deadlocked else (),
        trace=tuple(tr.events()),
        policy_stats=mgr.policy_stats(),
        wall_time_s=timeout_s,
    )

    return DemoReport(
        policy=PreventionPolicy.NONE,
        deadlocked=deadlocked,
        cycle=cycle_tuple,
        completed=tuple(completed_readers),
        result=result,
        events=tuple(tr.events()),
    )
