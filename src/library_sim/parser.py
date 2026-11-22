"""Input parsing for A2 and the Final Project (see library_sim.pyi).

The process section (N, Q and the 7-field reader rows) is parsed here. In
FINAL mode, any lines after the reader rows are handed to Samar's
``resource_parser.parse_resource_sections``. That module is imported
lazily, only in that branch [CONTRACT 6], so A2 mode works without it.
"""

from __future__ import annotations

import re
from typing import Literal

from .errors import InputError
from .models import SEAT_CAPACITY, ReaderSpec, SimulationInput

Mode = Literal["A2", "FINAL"]

_INT_RE = re.compile(r"[+-]?\d+")
READER_FIELDS = "ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY,SPACE_REQ,TABLE_REQ"


def parse_int(text: str, field: str, line_no: int | None) -> int:
    """Strict integer: optional sign and digits only, so "1_0", "1.0" and
    "" are rejected. Surrounding whitespace is ignored."""
    value = text.strip()
    if not _INT_RE.fullmatch(value):
        raise InputError(f"{field} must be an integer, got {value!r}", line_no)
    return int(value)


def parse_reader_row(line: str, line_no: int) -> ReaderSpec:
    """One ``ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY,SPACE_REQ,TABLE_REQ`` row."""
    parts = [p.strip() for p in line.split(",")]
    if len(parts) != 7:
        raise InputError(
            f"expected 7 fields {READER_FIELDS}, got {len(parts)}", line_no
        )
    pid, arrival_s, priority_s, service_s, category, space_s, table_s = parts

    if not pid:
        raise InputError("reader ID must not be empty", line_no)
    if any(ch.isspace() for ch in pid):
        raise InputError(f"reader ID {pid!r} must not contain whitespace", line_no)

    arrival = parse_int(arrival_s, "ARRIVAL", line_no)
    priority = parse_int(priority_s, "PRIORITY", line_no)
    service = parse_int(service_s, "SERVICE", line_no)
    space_req = parse_int(space_s, "SPACE_REQ", line_no)
    table_req = parse_int(table_s, "TABLE_REQ", line_no)

    if arrival < 0:
        raise InputError(f"ARRIVAL must be >= 0, got {arrival}", line_no)
    if priority < 1:
        raise InputError(f"PRIORITY must be >= 1, got {priority}", line_no)
    if service < 1:
        raise InputError(f"SERVICE must be >= 1, got {service}", line_no)
    if not category:
        raise InputError("CATEGORY must not be empty", line_no)
    if not 1 <= space_req <= SEAT_CAPACITY:
        raise InputError(
            f"SPACE_REQ must be between 1 and {SEAT_CAPACITY}, got {space_req}", line_no
        )
    if table_req != 0:
        raise InputError(f"TABLE_REQ must be 0 for the Library, got {table_req}", line_no)

    return ReaderSpec(pid, arrival, priority, service, category, space_req, table_req)


def parse_text(text: str, mode: Mode) -> SimulationInput:
    """Parse a whole A2 or Final input. Raises InputError (with line_no)."""
    if mode not in ("A2", "FINAL"):
        raise ValueError(f"mode must be 'A2' or 'FINAL', got {mode!r}")

    lines = text.splitlines()
    if lines and lines[0].startswith("﻿"):
        lines[0] = lines[0][1:]               # tolerate a UTF-8 byte-order mark
    while lines and not lines[-1].strip():
        lines.pop()                           # ignore trailing blank lines
    if not lines:
        raise InputError("input file is empty")

    n = parse_int(lines[0], "N", 1)
    if n < 1:
        raise InputError(f"N must be at least 1, got {n}", 1)
    if len(lines) < 2:
        raise InputError("missing the quantum Q on line 2", 2)
    quantum = parse_int(lines[1], "Q", 2)     # read and validated; Library has no Round Robin
    if quantum < 1:
        raise InputError(f"Q must be at least 1, got {quantum}", 2)
    if len(lines) < 2 + n:
        raise InputError(
            f"N is {n} but only {len(lines) - 2} reader row(s) follow", len(lines) + 1
        )

    readers: list[ReaderSpec] = []
    seen: set[str] = set()
    for index in range(2, 2 + n):
        spec = parse_reader_row(lines[index], index + 1)
        if spec.id in seen:
            raise InputError(f"duplicate reader ID {spec.id}", index + 1)
        seen.add(spec.id)
        readers.append(spec)

    next_index = 2 + n
    if next_index == len(lines):
        return SimulationInput(quantum=quantum, readers=tuple(readers))

    if mode == "A2":
        raise InputError(
            f"unexpected content after the {n} reader row(s) "
            "(resource sections are only allowed in the Final Project)",
            next_index + 1,
        )

    # FINAL mode: the R and K sections belong to Samar's resource_parser.
    from .resource_parser import parse_resource_sections  # [CONTRACT 6] lazy import

    resources, actions = parse_resource_sections(
        lines, next_index, tuple(readers)
    )
    return SimulationInput(
        quantum=quantum,
        readers=tuple(readers),
        resources=tuple(resources),
        actions=tuple(actions),
        has_resource_section=True,
    )


def parse_file(path: str, mode: Mode) -> SimulationInput:
    """Read UTF-8 text and parse it. A missing or unreadable file -> InputError."""
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        raise InputError(f"cannot open input file {path!r}: {exc.strerror}") from None
    except UnicodeDecodeError:
        raise InputError(f"input file {path!r} is not valid UTF-8 text") from None
    return parse_text(text, mode)
