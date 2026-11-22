"""Machine-readable output formats (see library_sim.pyi).

Graded formats: no header rows, no prose, '\\n' line endings, UTF-8.

PoolStats (memory.py), ResourceStats (resources.py) and CheckStats
(engine.py) are imported for type checking only. At run time any object
with the documented attributes works, so this module runs in the A2 zip
without the Final-only modules [CONTRACT 6] and can be tested without them.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Sequence

from .metrics import ProcessMetrics, SummaryMetrics

if TYPE_CHECKING:  # pragma: no cover
    from .engine import CheckStats
    from .memory import PoolStats
    from .resources import ResourceStats


def fmt_decimal(x: float) -> str:
    """Always 4 decimal places: 3.6667, 75.0000 (TA-approved). Never "-0.0000"."""
    if not math.isfinite(x):
        raise ValueError(f"cannot format non-finite statistic {x!r}")
    text = f"{x:.4f}"
    return "0.0000" if text == "-0.0000" else text


# ---------------------------------------------------------------------------
# A1 (identical to the C++ output.cpp)
# ---------------------------------------------------------------------------

def format_a1(metrics: Sequence[ProcessMetrics], summary: SummaryMetrics) -> str:
    """The exact C++ A1 output: a header row, one row per reader in ID order,
    then the SUMMARY block with 6 decimal places (std::fixed, setprecision(6))."""
    lines = ["PROCESS_ID,ARRIVAL,PRIORITY,SERVICE,START,COMPLETION,WAITING,TURNAROUND,RESPONSE"]
    for m in metrics:
        lines.append(
            f"{m.id},{m.arrival},{m.priority},{m.service},{m.start},"
            f"{m.completion},{m.waiting},{m.turnaround},{m.response}"
        )
    lines.append("SUMMARY")
    lines.append(f"AVERAGE_WAITING,{summary.average_waiting:.6f}")
    lines.append(f"AVERAGE_TURNAROUND,{summary.average_turnaround:.6f}")
    lines.append(f"AVERAGE_RESPONSE,{summary.average_response:.6f}")
    lines.append(f"THROUGHPUT,{summary.throughput:.6f}")
    lines.append(f"UTILIZATION,{summary.service_utilization_pct:.6f}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# A2 and Final
# ---------------------------------------------------------------------------

def _process_line(m: ProcessMetrics, with_resource_wait: bool) -> str:
    fields = [
        "PROCESS", m.id, m.arrival, m.priority, m.service, m.start, m.completion,
        m.waiting, m.turnaround, m.response, m.mem_admit, m.mem_wait, m.ready_wait,
    ]
    if with_resource_wait:
        fields.append(m.resource_wait)
    return ",".join(str(f) for f in fields)


def _summary_lines(summary: SummaryMetrics) -> list[str]:
    return [
        f"SUMMARY,AVERAGE_WAITING,{fmt_decimal(summary.average_waiting)}",
        f"SUMMARY,AVERAGE_TURNAROUND,{fmt_decimal(summary.average_turnaround)}",
        f"SUMMARY,AVERAGE_RESPONSE,{fmt_decimal(summary.average_response)}",
        f"SUMMARY,THROUGHPUT,{fmt_decimal(summary.throughput)}",
        f"SUMMARY,SERVICE_UTILIZATION_PCT,{fmt_decimal(summary.service_utilization_pct)}",
        f"SUMMARY,AVERAGE_MEMORY_WAIT,{fmt_decimal(summary.average_memory_wait)}",
        f"SUMMARY,COMPLETED_COUNT,{summary.completed_count}",
        f"SUMMARY,BLOCKED_FOR_MEMORY_COUNT,{summary.blocked_for_memory_count}",
    ]


def _pool_line(pool: PoolStats) -> str:
    return (
        f"POOL,{pool.name},{pool.capacity},{pool.peak_occupied},"
        f"{fmt_decimal(pool.utilization_pct)},{pool.max_ext_frag}"
    )


def _sorted_by_id(metrics: Sequence[ProcessMetrics]) -> list[ProcessMetrics]:
    # compute_process_metrics already sorts; sort again so the output is
    # correct even if a caller passes metrics in another order.
    return sorted(metrics, key=lambda m: m.id)


def format_a2(metrics: Sequence[ProcessMetrics], summary: SummaryMetrics,
              pool: PoolStats) -> str:
    """PROCESS lines (ascending ID), the 8 SUMMARY lines, then the POOL line."""
    lines = [_process_line(m, with_resource_wait=False) for m in _sorted_by_id(metrics)]
    lines += _summary_lines(summary)
    lines.append(_pool_line(pool))
    return "\n".join(lines) + "\n"


def format_final(metrics: Sequence[ProcessMetrics], summary: SummaryMetrics,
                 pool: PoolStats, resources: Sequence[ResourceStats],
                 checks: CheckStats) -> str:
    """A2 lines with RESOURCE_WAIT appended to each PROCESS line, then one
    RESOURCE line per declared resource (sorted by ID), then three CHECK lines.
    CHECK lines are emitted even for resource-free inputs (TA-approved)."""
    lines = [_process_line(m, with_resource_wait=True) for m in _sorted_by_id(metrics)]
    lines += _summary_lines(summary)
    lines.append(_pool_line(pool))
    for r in sorted(resources, key=lambda r: r.resource_id):
        lines.append(
            f"RESOURCE,{r.resource_id},{r.capacity},{r.max_simultaneous_holders},"
            f"{r.acquisitions},{r.wait_events}"
        )
    lines.append(f"CHECK,EXCLUSIVITY_VIOLATIONS,{checks.exclusivity_violations}")
    lines.append(f"CHECK,UNRESOLVED_DEADLOCKS,{checks.unresolved_deadlocks}")
    lines.append(f"CHECK,COMPLETED_COUNT,{checks.completed_count}")
    return "\n".join(lines) + "\n"


def write_output(path: str, text: str) -> None:
    """Write UTF-8 text with '\\n' line endings on every platform."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
