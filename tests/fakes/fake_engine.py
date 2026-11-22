"""Deterministic engine stand-in for downstream owners.

This fake has no dependency on ``memory`` or any Final module.  It lets
experiments and resource work exercise result plumbing before the real engine
is integrated.
"""

from __future__ import annotations

from dataclasses import dataclass

from library_sim.models import Allocator, ReaderResult, Scheduler, SimulationInput


@dataclass(frozen=True)
class PoolStatsFake:
    name: str = "SPACE"
    capacity: int = 6
    peak_occupied: int = 1
    occupied_integral: int = 1
    max_ext_frag: int = 0
    start_time: int = 0
    end_time: int = 1

    @property
    def utilization_pct(self) -> float:
        return 100.0 / 6.0


@dataclass(frozen=True)
class SimulationResultFake:
    readers: tuple[ReaderResult, ...]
    incomplete: tuple[str, ...]
    pool: PoolStatsFake
    resources: tuple[object, ...] = ()
    checks: object | None = None
    deadlock_cycles: tuple[tuple[str, ...], ...] = ()
    trace: tuple[object, ...] = ()
    policy_stats: object | None = None
    wall_time_s: float = 0.0


def simulate(
    inp: SimulationInput,
    scheduler: Scheduler,
    allocator: Allocator,
    mode: str,
    **kwargs: object,
) -> SimulationResultFake:
    """Return one deterministic completed reader as a fixed valid result."""
    del scheduler, allocator, mode, kwargs
    spec = sorted(inp.readers, key=lambda reader: reader.id)[0]
    result = ReaderResult(
        spec.id,
        spec.arrival,
        spec.priority,
        spec.service,
        spec.arrival,
        spec.arrival + spec.service,
        spec.arrival,
    )
    return SimulationResultFake((result,), (), PoolStatsFake())
