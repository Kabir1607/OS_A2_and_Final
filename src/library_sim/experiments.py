"""Repeatable comparisons for Aarush A7: seat placement and book policies.

This module reports observations, not graded simulation output. Final-only
imports stay inside Final branches so allocator comparisons also run in A2.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, fields
from pathlib import Path
import statistics
import sys
from typing import TYPE_CHECKING, Literal, Sequence

from .engine import CheckStats, simulate
from .errors import InputError
from .memory import PoolStats
from .metrics import SummaryMetrics, compute_process_metrics, compute_summary
from .models import Allocator, Scheduler, SimulationInput
from .parser import parse_file

if TYPE_CHECKING:
    from .deadlock import PolicyStats, PreventionPolicy
    from .resources import ResourceStats


@dataclass(frozen=True)
class RunSummary:
    """One completed run: service/seat metrics and optional book-policy counters."""
    input_name: str
    scheduler: Scheduler
    allocator: Allocator
    policy: PreventionPolicy | None
    summary: SummaryMetrics
    pool: PoolStats
    total_resource_wait: int
    max_resource_wait: int
    resources: tuple[ResourceStats, ...]
    policy_stats: PolicyStats | None
    checks: CheckStats | None
    wall_time_s: float


def run_once(inp: SimulationInput, input_name: str, scheduler: Scheduler,
             allocator: Allocator, mode: Literal['A2', 'FINAL'],
             policy: PreventionPolicy | None = None) -> RunSummary:
    """Run a workload and reject unsafe or unfinished results before reporting.

    In Final mode a memory-only tracer enables independent ownership replay.
    Wall time therefore includes that same instrumentation for both policies.
    """
    tracer = None
    if mode == 'FINAL':
        from .deadlock import DEFAULT_POLICY
        from .trace import Tracer
        policy = policy or DEFAULT_POLICY
        tracer = Tracer(enabled=True)
    else:
        policy = None
    result = simulate(inp, scheduler, allocator, mode, policy=policy, tracer=tracer)
    ids = [r.id for r in result.readers]
    if result.incomplete or len(ids) != inp.n or set(ids) != {r.id for r in inp.readers}:
        raise ValueError(f'{input_name}: experiment did not complete every reader exactly once')
    if mode == 'FINAL':
        c = result.checks
        if c is None or c.completed_count != inp.n or c.exclusivity_violations or c.unresolved_deadlocks:
            raise ValueError(f'{input_name}: experiment failed its safety checks')
    metrics = compute_process_metrics(result.readers)
    waits = [r.resource_wait for r in result.readers]
    return RunSummary(input_name, scheduler, allocator, policy, compute_summary(metrics),
                      result.pool, sum(waits), max(waits, default=0), result.resources,
                      result.policy_stats, result.checks, result.wall_time_s)


def compare_allocators(inp: SimulationInput, input_name: str) -> list[RunSummary]:
    """Compare two librarian schedulers with three seat policies: six A2 runs."""
    return [run_once(inp, input_name, scheduler, allocator, 'A2')
            for scheduler in Scheduler for allocator in Allocator]


@dataclass(frozen=True)
class Spread:
    """Mean and observed extremes of one metric over repeated runs."""
    mean: float
    min: float
    max: float


@dataclass(frozen=True)
class PolicyComparisonRow:
    """One input/scheduler/policy cell, including observed variability."""
    input_name: str
    scheduler: Scheduler
    allocator: Allocator
    policy: PreventionPolicy
    runs: int
    all_completed: bool
    all_safe: bool
    average_waiting: Spread
    average_turnaround: Spread
    throughput: Spread
    service_utilization_pct: Spread
    total_resource_wait: Spread
    max_resource_wait: Spread
    acquisitions: Spread
    wait_events: Spread
    rollbacks: Spread
    resources_rolled_back: Spread
    held_while_waiting: Spread
    wall_time_s: Spread


# The order matches the Spread fields above and is also the report column order.
POLICY_METRICS = (
    'average_waiting', 'average_turnaround', 'throughput', 'service_utilization_pct',
    'total_resource_wait', 'max_resource_wait', 'acquisitions', 'wait_events',
    'rollbacks', 'resources_rolled_back', 'held_while_waiting', 'wall_time_s',
)


def _policy_values(run: RunSummary) -> list[float]:
    """Collect like-for-like numbers; a resource-free run has zero counters."""
    stats = run.policy_stats
    return [run.summary.average_waiting, run.summary.average_turnaround,
            run.summary.throughput, run.summary.service_utilization_pct,
            run.total_resource_wait, run.max_resource_wait,
            sum(r.acquisitions for r in run.resources),
            sum(r.wait_events for r in run.resources),
            stats.rollbacks if stats else 0,
            stats.resources_rolled_back if stats else 0,
            stats.held_while_waiting if stats else 0, run.wall_time_s]


def compare_policies(
    inputs: Sequence[tuple[str, SimulationInput]],
    policies: Sequence[PreventionPolicy] = (),
    schedulers: Sequence[Scheduler] = (Scheduler.FCFS, Scheduler.PRIORITY),
    allocator: Allocator = Allocator.FIRST_FIT,
    repeats: int = 30,
) -> list[PolicyComparisonRow]:
    """Repeat each policy cell; publish nothing if any constituent run fails.

    The empty policy argument resolves lazily to both safe policies. This
    avoids importing deadlock.py just to import the A2 comparison functions.
    """
    from .deadlock import PreventionPolicy
    if repeats < 1:
        raise ValueError('repeats must be positive')
    if not policies:
        policies = (PreventionPolicy.ROLLBACK, PreventionPolicy.ORDERED)
    rows = []
    for name, inp in inputs:
        for scheduler in schedulers:
            for policy in policies:
                observations = []
                for _ in range(repeats):
                    observations.append(_policy_values(run_once(inp, name, scheduler, allocator,
                                                               'FINAL', policy)))
                spreads = []
                for column in zip(*observations):
                    spreads.append(Spread(statistics.fmean(column), min(column), max(column)))
                rows.append(PolicyComparisonRow(name, scheduler, allocator, policy, repeats,
                                                True, True, *spreads))
    return rows


def better_policy_by_metric(rows: Sequence[PolicyComparisonRow]
                            ) -> dict[tuple[str, Scheduler, str], PreventionPolicy | None]:
    """Compare means per workload/scheduler; differences below 1e-3 are ties.

    Lower is better except throughput and service utilization. A best-value
    tie returns None, including when additional policies were supplied.
    """
    result = {}
    groups: dict[tuple[str, Scheduler], list[PolicyComparisonRow]] = {}
    for row in rows:
        if not row.all_safe or not row.all_completed:
            raise ValueError('cannot rank an unsafe or incomplete experiment')
        groups.setdefault((row.input_name, row.scheduler), []).append(row)
    for key, group in groups.items():
        for metric in POLICY_METRICS:
            reverse = metric in ('throughput', 'service_utilization_pct')
            ordered = sorted(group, key=lambda r:getattr(r, metric).mean, reverse=reverse)
            winner = ordered[0].policy
            if len(ordered) > 1:
                difference = abs(getattr(ordered[0], metric).mean-getattr(ordered[1], metric).mean)
                if difference < 1e-3:
                    winner = None
            result[(*key, metric)] = winner
    return result


def _cell(value: object) -> str:
    """Format report values safely; keep wall-clock precision in Spread cells."""
    if isinstance(value, Spread):
        return f'{value.mean:.6f} [{value.min:.6f}, {value.max:.6f}]'
    if isinstance(value, float):
        return f'{value:.4f}'
    return str(value).replace('|', r'\|').replace('\n', ' ')


def format_markdown(rows: Sequence[RunSummary] | Sequence[PolicyComparisonRow]) -> str:
    """Build tables without modifying simulation output or rounding raw results."""
    if not rows:
        return ''
    if isinstance(rows[0], RunSummary):
        headers = ['Input', 'Scheduler', 'Allocator']
        headers += [f.name for f in fields(SummaryMetrics)]
        headers += ['peak_occupied', 'pool_utilization_pct', 'max_ext_frag', 'last_completion']
        values = []
        for r in rows:
            values.append([r.input_name, r.scheduler.value, r.allocator.value]
                          + [getattr(r.summary, f.name) for f in fields(SummaryMetrics)]
                          + [r.pool.peak_occupied, r.pool.utilization_pct,
                             r.pool.max_ext_frag, r.pool.end_time])
    else:
        headers = ['Input', 'Scheduler', 'Allocator', 'Policy', 'Runs', 'All completed', 'All safe']
        headers += list(POLICY_METRICS)
        values = [[r.input_name, r.scheduler.value, r.allocator.value, r.policy.value,
                   r.runs, r.all_completed, r.all_safe]
                  + [getattr(r, metric) for metric in POLICY_METRICS] for r in rows]
    lines = ['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |']
    lines += ['| '+' | '.join(_cell(v) for v in row)+' |' for row in values]
    return '\n'.join(lines)+'\n'


class _Arguments(argparse.ArgumentParser):
    """Match the project's Error: stderr convention instead of printing a traceback."""
    def error(self, message: str) -> None:
        raise ValueError(message)


def main(argv: Sequence[str] | None = None) -> int:
    """Run repeatable comparisons; --md writes only the completed report file."""
    parser = _Arguments(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    allocators = sub.add_parser('allocators')
    allocators.add_argument('input')
    allocators.add_argument('--md')
    policies = sub.add_parser('policies')
    policies.add_argument('inputs', nargs='+')
    policies.add_argument('--repeats', type=int, default=30)
    policies.add_argument('--md')
    try:
        args = parser.parse_args(argv)
        if args.command == 'allocators':
            rows = compare_allocators(parse_file(args.input, 'A2'), Path(args.input).name)
        else:
            inputs = [(Path(p).name, parse_file(p, 'FINAL')) for p in args.inputs]
            rows = compare_policies(inputs, repeats=args.repeats)
        report = format_markdown(rows)
        if args.md:
            Path(args.md).write_text(report, encoding='utf-8')
        else:
            print(report, end='')
        return 0
    except (InputError, ImportError, OSError, ValueError, AssertionError, RuntimeError) as exc:
        print(f'Error: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
