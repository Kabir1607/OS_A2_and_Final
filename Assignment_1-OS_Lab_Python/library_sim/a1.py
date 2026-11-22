"""Assignment 1: a faithful Python port of the C++ Smart Library simulator.

C++ file          ->  Python
input.cpp         ->  read_a1_input / parse_a1_text   (here)
fcfs.cpp          ->  fcfs                            (here)
priority.cpp      ->  priority_schedule               (here)
metrics.cpp       ->  library_sim.metrics
output.cpp        ->  library_sim.output.format_a1
main.cpp          ->  a1_main                         (here)

On valid input the output is byte-for-byte identical to the C++ program.
Unlike the C++ version, malformed input gives a clear error instead of a crash.

Usage:  python3 -m library_sim.a1 INPUT_FILE FCFS|PRIORITY
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Sequence

from .errors import InputError, UsageError
from .metrics import compute_process_metrics, compute_summary
from .models import NUM_LIBRARIANS, ReaderResult, ReaderSpec, Scheduler
from .output import format_a1
from .scheduler import fcfs_key, priority_key


@dataclass(frozen=True)
class A1Result:
    spec: ReaderSpec
    start: int
    completion: int


# ---------------------------------------------------------------------------
# Input (input.cpp)
# ---------------------------------------------------------------------------

def _parse_int(text: str, field: str, line_no: int) -> int:
    try:
        return int(text.strip())
    except ValueError:
        raise InputError(f"{field} must be an integer, got {text.strip()!r}", line_no) from None


def parse_a1_text(text: str) -> list[ReaderSpec]:
    """Parse the A1 format: N, Q, then N rows of ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY.

    As in the C++ reader, CATEGORY is the rest of the row and anything after
    the N reader rows is ignored. Raises InputError on malformed input.
    """
    lines = text.splitlines()
    while lines and not lines[-1].strip():
        lines.pop()                      # ignore trailing blank lines
    if not lines:
        raise InputError("input file is empty")

    n = _parse_int(lines[0], "N", 1)
    if n < 1:
        raise InputError(f"N must be at least 1, got {n}", 1)
    if len(lines) < 2:
        raise InputError("missing the quantum Q on line 2", 2)
    q = _parse_int(lines[1], "Q", 2)     # read and validated; Library has no Round Robin
    if q < 1:
        raise InputError(f"Q must be at least 1, got {q}", 2)
    if len(lines) < 2 + n:
        raise InputError(f"expected {n} reader rows, found {len(lines) - 2}", len(lines) + 1)

    readers: list[ReaderSpec] = []
    seen: set[str] = set()
    for line_no in range(3, 3 + n):
        line = lines[line_no - 1]
        parts = line.split(",", 4)
        if len(parts) != 5:
            raise InputError("expected ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY", line_no)
        pid = parts[0].strip()
        if not pid or any(ch.isspace() for ch in pid):
            raise InputError(f"invalid reader ID {parts[0]!r}", line_no)
        if pid in seen:
            raise InputError(f"duplicate reader ID {pid}", line_no)
        arrival = _parse_int(parts[1], "ARRIVAL", line_no)
        priority = _parse_int(parts[2], "PRIORITY", line_no)
        service = _parse_int(parts[3], "SERVICE", line_no)
        category = parts[4].strip()
        if arrival < 0:
            raise InputError(f"ARRIVAL must be >= 0, got {arrival}", line_no)
        if priority < 1:
            raise InputError(f"PRIORITY must be >= 1, got {priority}", line_no)
        if service < 1:
            raise InputError(f"SERVICE must be >= 1, got {service}", line_no)
        if not category:
            raise InputError("CATEGORY must not be empty", line_no)
        seen.add(pid)
        readers.append(ReaderSpec(pid, arrival, priority, service, category))
    return readers


def read_a1_input(path: str) -> list[ReaderSpec]:
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        raise InputError(f"cannot open input file {path!r}: {exc.strerror}") from None
    except UnicodeDecodeError:
        raise InputError(f"input file {path!r} is not valid UTF-8 text") from None
    return parse_a1_text(text)


# ---------------------------------------------------------------------------
# Scheduling (fcfs.cpp, priority.cpp)
# ---------------------------------------------------------------------------

def _earliest_free(available_at: list[int]) -> int:
    """The librarian who becomes free first; librarian 0 wins ties."""
    return 0 if available_at[0] <= available_at[1] else 1


def fcfs(readers: Sequence[ReaderSpec]) -> list[A1Result]:
    """Serve readers in (arrival, ID) order, each on the librarian who frees
    up first, starting once both the reader and the librarian are available."""
    available_at = [0] * NUM_LIBRARIANS
    results: list[A1Result] = []
    for spec in sorted(readers, key=fcfs_key):
        lib = _earliest_free(available_at)
        start = max(available_at[lib], spec.arrival)
        completion = start + spec.service
        available_at[lib] = completion
        results.append(A1Result(spec, start, completion))
    return results


def priority_schedule(readers: Sequence[ReaderSpec]) -> list[A1Result]:
    """Non-preemptive priority: whenever a librarian frees up, serve the
    arrived reader with the best (priority, arrival, ID); if nobody has
    arrived yet, jump the clock to the next arrival."""
    available_at = [0] * NUM_LIBRARIANS
    pending = list(readers)
    results: list[A1Result] = []
    while pending:
        # 1. The librarian who becomes free first.
        lib = _earliest_free(available_at)
        current_time = available_at[lib]

        # 2. Nobody has arrived yet: jump to the earliest arrival.
        if not any(p.arrival <= current_time for p in pending):
            current_time = min(p.arrival for p in pending)

        # 3. Best arrived reader by priority -> arrival -> ID.
        best_index = min(
            (i for i, p in enumerate(pending) if p.arrival <= current_time),
            key=lambda i: priority_key(pending[i]),
        )
        best = pending.pop(best_index)

        # 4. Serve it to completion.
        start = current_time
        completion = start + best.service
        available_at[lib] = completion
        results.append(A1Result(best, start, completion))
    return results


def run_a1(readers: Sequence[ReaderSpec], scheduler: Scheduler) -> list[A1Result]:
    if scheduler is Scheduler.FCFS:
        return fcfs(readers)
    return priority_schedule(readers)


def to_reader_results(results: Sequence[A1Result]) -> list[ReaderResult]:
    """A1 has no memory or resources: M = A and RESOURCE_WAIT = 0."""
    return [
        ReaderResult(
            id=r.spec.id,
            arrival=r.spec.arrival,
            priority=r.spec.priority,
            service=r.spec.service,
            start=r.start,
            completion=r.completion,
            mem_admit=r.spec.arrival,
        )
        for r in results
    ]


def simulate_a1_text(text: str, scheduler: Scheduler) -> str:
    """Whole pipeline on input text; returns the A1 output text."""
    results = run_a1(parse_a1_text(text), scheduler)
    metrics = compute_process_metrics(to_reader_results(results))
    return format_a1(metrics, compute_summary(metrics))


# ---------------------------------------------------------------------------
# CLI (main.cpp)
# ---------------------------------------------------------------------------

USAGE = "Usage: python3 main.py INPUT_FILE FCFS|PRIORITY"


def a1_main(argv: Sequence[str]) -> int:
    """`argv` are the arguments AFTER the program name. Prints the A1 result
    to stdout; errors go to stderr. Returns the exit code (0 ok, 1 error)."""
    try:
        if len(argv) != 2:
            raise UsageError(USAGE)
        input_file, algorithm = argv
        try:
            scheduler = Scheduler(algorithm)   # case-sensitive, like the C++ version
        except ValueError:
            raise UsageError(f"unknown algorithm {algorithm!r}: choose FCFS or PRIORITY") from None

        readers = read_a1_input(input_file)
        results = run_a1(readers, scheduler)
        metrics = compute_process_metrics(to_reader_results(results))
        sys.stdout.write(format_a1(metrics, compute_summary(metrics)))
        return 0
    except (UsageError, InputError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(a1_main(sys.argv[1:]))
