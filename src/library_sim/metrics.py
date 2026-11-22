"""Metrics: pure functions from raw timestamps to numbers.

Port of the C++ metrics.cpp, extended with the A2/Final fields defined in
library_sim.pyi. For A1, MEM_ADMIT = ARRIVAL and RESOURCE_WAIT = 0, so
MEM_WAIT = 0 and READY_WAIT = WAITING.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .models import NUM_LIBRARIANS, ReaderResult


@dataclass(frozen=True)
class ProcessMetrics:
    id: str
    arrival: int
    priority: int
    service: int
    start: int
    completion: int
    waiting: int        # C - A - B
    turnaround: int     # C - A
    response: int       # S - A
    mem_admit: int      # M
    mem_wait: int       # M - A
    ready_wait: int     # waiting - mem_wait - resource_wait
    resource_wait: int


@dataclass(frozen=True)
class SummaryMetrics:
    average_waiting: float
    average_turnaround: float
    average_response: float
    throughput: float                # N / E, E = max C - min A
    service_utilization_pct: float   # sum B / (librarians * E) * 100
    average_memory_wait: float
    completed_count: int
    blocked_for_memory_count: int    # readers with M > A


def compute_process_metrics(results: Iterable[ReaderResult]) -> list[ProcessMetrics]:
    """Per-reader metrics, sorted by ID in plain string order."""
    metrics: list[ProcessMetrics] = []
    for r in results:
        turnaround = r.completion - r.arrival
        waiting = turnaround - r.service
        mem_wait = r.mem_admit - r.arrival
        ready_wait = waiting - mem_wait - r.resource_wait
        if not (r.arrival <= r.mem_admit <= r.start <= r.completion):
            raise AssertionError(f"{r.id}: expected A <= M <= S <= C, got {r}")
        if waiting < 0 or ready_wait < 0 or r.resource_wait < 0:
            raise AssertionError(f"{r.id}: negative waiting component, got {r}")
        metrics.append(ProcessMetrics(
            id=r.id,
            arrival=r.arrival,
            priority=r.priority,
            service=r.service,
            start=r.start,
            completion=r.completion,
            waiting=waiting,
            turnaround=turnaround,
            response=r.start - r.arrival,
            mem_admit=r.mem_admit,
            mem_wait=mem_wait,
            ready_wait=ready_wait,
            resource_wait=r.resource_wait,
        ))
    metrics.sort(key=lambda m: m.id)
    return metrics


def compute_summary(metrics: Sequence[ProcessMetrics],
                    num_librarians: int = NUM_LIBRARIANS) -> SummaryMetrics:
    """Overall metrics. E is measured from the first arrival to the last
    completion (the same window as throughput), as in the C++ A1."""
    if not metrics:
        return SummaryMetrics(0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0, 0)

    n = float(len(metrics))
    total_waiting = sum(m.waiting for m in metrics)
    total_turnaround = sum(m.turnaround for m in metrics)
    total_response = sum(m.response for m in metrics)
    total_mem_wait = sum(m.mem_wait for m in metrics)
    busy_time = sum(m.service for m in metrics)
    first_arrival = min(m.arrival for m in metrics)
    last_completion = max(m.completion for m in metrics)

    # Always positive for valid input, since every service time is >= 1.
    elapsed = float(last_completion - first_arrival)

    # Same operation order as the C++ code, so the doubles round identically.
    return SummaryMetrics(
        average_waiting=total_waiting / n,
        average_turnaround=total_turnaround / n,
        average_response=total_response / n,
        throughput=n / elapsed,
        service_utilization_pct=busy_time / (num_librarians * elapsed) * 100.0,
        average_memory_wait=total_mem_wait / n,
        completed_count=len(metrics),
        blocked_for_memory_count=sum(1 for m in metrics if m.mem_admit > m.arrival),
    )
