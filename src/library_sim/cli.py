"""Command-line entry points for the A2 and Final submissions.

The two public functions return process-style exit codes instead of calling
``sys.exit``.  This makes them directly testable and lets each packaged
``main.py`` remain a tiny adapter.
"""

from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter
from typing import Sequence, TextIO

from .errors import InputError, UsageError
from .models import Allocator, Scheduler


def _error(exc: Exception) -> int:
    """Print the repository-standard error form and return status 1."""
    print(f"Error: {exc}", file=sys.stderr)
    return 1


def _enums(scheduler_text: str, allocator_text: str) -> tuple[Scheduler, Allocator]:
    """Parse case-sensitive enum values while normalizing their error."""
    try:
        return Scheduler(scheduler_text), Allocator(allocator_text)
    except ValueError as exc:
        raise UsageError(
            "scheduler must be FCFS or PRIORITY and allocator must be "
            "FIRST_FIT, BEST_FIT, or WORST_FIT"
        ) from exc


def a2_main(argv: Sequence[str]) -> int:
    """Run A2: ``INPUT SCHEDULER ALLOCATOR OUTPUT``."""
    if len(argv) != 4:
        return _error(UsageError(
            "usage: main.py INPUT_FILE FCFS|PRIORITY "
            "FIRST_FIT|BEST_FIT|WORST_FIT OUTPUT_FILE"
        ))
    try:
        scheduler, allocator = _enums(argv[1], argv[2])
        from .engine import simulate
        from .metrics import compute_process_metrics, compute_summary
        from .output import format_a2, write_output
        from .parser import parse_file

        inp = parse_file(argv[0], "A2")
        result = simulate(inp, scheduler, allocator, "A2")
        if result.incomplete:
            raise InputError(
                f"simulation ended with unfinished readers: "
                f"{', '.join(result.incomplete)}"
            )
        metrics = compute_process_metrics(result.readers)
        write_output(argv[3], format_a2(metrics, compute_summary(metrics), result.pool))
        return 0
    except (InputError, UsageError, OSError, ValueError, AssertionError) as exc:
        return _error(exc)


def _open_trace(path: str) -> tuple[TextIO | None, bool]:
    """Open a trace destination, returning ``(sink, should_close)``."""
    if path == "-":
        return sys.stderr, False
    return open(path, "w", encoding="utf-8", newline="\n"), True


def final_main(argv: Sequence[str]) -> int:
    """Run Final mode and optionally print traces or policy statistics."""
    if argv and argv[0] == "--demo-deadlock":
        return _demo_deadlock(argv[1:])
    if len(argv) < 4:
        return _error(UsageError(
            "usage: main.py INPUT_FILE SCHEDULER ALLOCATOR OUTPUT_FILE "
            "[--trace FILE|-] [--policy ROLLBACK|ORDERED] [--stats] [--quiet]"
        ))

    input_path, scheduler_text, allocator_text, output_path = argv[:4]
    flags = list(argv[4:])
    trace_path: str | None = None
    policy_text: str | None = None
    stats = False
    quiet = False
    i = 0
    while i < len(flags):
        flag = flags[i]
        if flag == "--trace" and i + 1 < len(flags):
            trace_path = flags[i + 1]
            i += 2
        elif flag == "--policy" and i + 1 < len(flags):
            policy_text = flags[i + 1]
            i += 2
        elif flag == "--stats":
            stats = True
            i += 1
        elif flag == "--quiet":
            quiet = True
            i += 1
        else:
            return _error(UsageError(f"unknown or incomplete option {flag!r}"))

    sink: TextIO | None = None
    close_sink = False
    started = perf_counter()
    try:
        scheduler, allocator = _enums(scheduler_text, allocator_text)
        from .deadlock import PreventionPolicy
        from .engine import simulate
        from .metrics import compute_process_metrics, compute_summary
        from .output import format_final, write_output
        from .parser import parse_file
        from .trace import Tracer

        policy = None
        if policy_text is not None:
            try:
                policy = PreventionPolicy(policy_text)
            except ValueError as exc:
                raise UsageError("policy must be ROLLBACK or ORDERED") from exc
        if trace_path is not None:
            sink, close_sink = _open_trace(trace_path)
        tracer = Tracer(sink=sink, enabled=trace_path is not None)
        result = simulate(
            parse_file(input_path, "FINAL"),
            scheduler,
            allocator,
            "FINAL",
            policy=policy,
            tracer=tracer,
        )
        metrics = compute_process_metrics(result.readers)
        if result.checks is None:
            raise AssertionError("Final simulation did not provide CHECK statistics")
        write_output(
            output_path,
            format_final(metrics, compute_summary(metrics), result.pool,
                         result.resources, result.checks),
        )
        if stats and not quiet:
            print(f"wall_time_s={perf_counter() - started:.6f}", file=sys.stderr)
        if result.incomplete:
            return 2
        return 0
    except (InputError, UsageError, OSError, ValueError, AssertionError) as exc:
        return _error(exc)
    finally:
        if close_sink and sink is not None:
            sink.close()


def _demo_deadlock(argv: Sequence[str]) -> int:
    """Delegate the bounded demonstration to Samar's real implementation."""
    if len(argv) > 3:
        return _error(UsageError(
            "usage: main.py --demo-deadlock [INPUT_FILE] "
            "[--policy NONE|ROLLBACK|ORDERED]"
        ))
    try:
        from .deadlock import PreventionPolicy, run_unsafe_demo

        input_path: str | None = None
        selected: PreventionPolicy | None = None
        i = 0
        while i < len(argv):
            if argv[i] == "--policy" and i + 1 < len(argv):
                selected = PreventionPolicy(argv[i + 1])
                i += 2
            elif argv[i].startswith("--"):
                raise UsageError(f"unknown option {argv[i]!r}")
            elif input_path is None:
                input_path = argv[i]
                i += 1
            else:
                raise UsageError("only one demo input path is allowed")
        policies = (selected,) if selected is not None else (
            PreventionPolicy.NONE,
            PreventionPolicy.ROLLBACK,
            PreventionPolicy.ORDERED,
        )
        reports = run_unsafe_demo(
            policies=policies,
            **({"input_path": input_path} if input_path is not None else {}),
        )
        for report in reports:
            print(
                f"{report.policy.value}: deadlocked={report.deadlocked} "
                f"completed={','.join(report.completed)}"
            )
        return 0
    except (InputError, UsageError, OSError, ValueError) as exc:
        return _error(exc)
