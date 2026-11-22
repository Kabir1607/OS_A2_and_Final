"""Machine-readable output formats.

Only the A1 format is needed for this port. The A2 and Final writers
(format_a2, format_final) will be added here as specified in library_sim.pyi.
"""

from __future__ import annotations

from typing import Sequence

from .metrics import ProcessMetrics, SummaryMetrics


def fmt_decimal(x: float) -> str:
    """A2/Final decimal format: always 4 decimal places (TA-approved)."""
    return f"{x:.4f}"


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


def write_output(path: str, text: str) -> None:
    """Write UTF-8 text with '\\n' line endings on every platform."""
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
