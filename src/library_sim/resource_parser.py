"""Resource and action section parsing for the Final Project.

Parses the R and K sections following the reader rows and performs static
semantic validation on resource actions.
"""

from __future__ import annotations

import re
from typing import Sequence

from .errors import InputError
from .models import STANDARD_RESOURCES, Action, ActionType, ReaderSpec, ResourceSpec

_INT_RE = re.compile(r"[+-]?\d+")


def _parse_int(text: str, field: str, line_no: int | None = None) -> int:
    """Strict integer parsing matching parser.py."""
    value = text.strip()
    if not _INT_RE.fullmatch(value):
        raise InputError(f"{field} must be an integer, got {value!r}", line_no)
    return int(value)


def validate_actions(
    readers: Sequence[ReaderSpec],
    resources: Sequence[ResourceSpec],
    actions: Sequence[Action],
) -> None:
    """Static checks, InputError on failure:
      * resource IDs unique, in STANDARD_RESOURCES, CAPACITY == 1
      * reader IDs exist, resource IDs declared, UNITS == 1, 0 <= offset <= SERVICE
      * replaying each reader's own actions (sorted by offset, row):
        no RELEASE of something it doesn't hold, no ACQUIRE of something
        it already holds, and nothing still held at the end.
    """
    seen_resources: set[str] = set()
    for res in resources:
        if res.id in seen_resources:
            raise InputError(f"duplicate resource ID {res.id!r}")
        if res.id not in STANDARD_RESOURCES:
            raise InputError(f"resource {res.id!r} not in STANDARD_RESOURCES")
        if res.capacity != 1:
            raise InputError(f"CAPACITY must be 1 for Library, got {res.capacity}")
        seen_resources.add(res.id)

    reader_map = {r.id: r for r in readers}
    for action in actions:
        if action.reader_id not in reader_map:
            raise InputError(f"unknown reader ID {action.reader_id!r} in action")
        if action.resource_id not in seen_resources:
            raise InputError(f"undeclared resource ID {action.resource_id!r} in action")
        if action.units != 1:
            raise InputError(f"UNITS must be 1, got {action.units}")
        reader = reader_map[action.reader_id]
        if not (0 <= action.work_offset <= reader.service):
            raise InputError(
                f"WORK_OFFSET {action.work_offset} outside 0..{reader.service} for reader {reader.id}"
            )

    # Replay each reader's actions
    for reader in readers:
        reader_actions = sorted(
            [a for a in actions if a.reader_id == reader.id],
            key=lambda a: (a.work_offset, a.row_index),
        )
        held: set[str] = set()
        for action in reader_actions:
            if action.action == ActionType.ACQUIRE:
                if action.resource_id in held:
                    raise InputError(
                        f"reader {reader.id} double-acquired resource {action.resource_id!r}"
                    )
                held.add(action.resource_id)
            elif action.action == ActionType.RELEASE:
                if action.resource_id not in held:
                    raise InputError(
                        f"reader {reader.id} released unheld resource {action.resource_id!r}"
                    )
                held.remove(action.resource_id)
        if held:
            raise InputError(
                f"reader {reader.id} still holds resources at completion: {', '.join(sorted(held))}"
            )


def parse_resource_sections(
    lines: Sequence[str],
    start: int,
    readers: Sequence[ReaderSpec],
) -> tuple[tuple[ResourceSpec, ...], tuple[Action, ...]]:
    """Parse `R`, R rows of RESOURCE_ID,CAPACITY, `K`, K rows of
    ID,WORK_OFFSET,ACTION,RESOURCE_ID,UNITS, starting at lines[start]
    (0-based index). If R is present, K and both row counts must be too.
    Then calls validate_actions. Raises InputError (with line_no).
    """
    if start >= len(lines):
        raise InputError("missing resource count R", start + 1)

    r_count = _parse_int(lines[start], "R", start + 1)
    if r_count < 0:
        raise InputError(f"R must be non-negative, got {r_count}", start + 1)

    if len(lines) < start + 1 + r_count:
        raise InputError(
            f"R is {r_count} but only {len(lines) - start - 1} resource row(s) follow",
            len(lines) + 1,
        )

    declared_resources: list[ResourceSpec] = []
    seen_resources: set[str] = set()
    for idx in range(start + 1, start + 1 + r_count):
        line_no = idx + 1
        parts = [p.strip() for p in lines[idx].split(",")]
        if len(parts) != 2:
            raise InputError(
                f"expected 2 fields (RESOURCE_ID,CAPACITY), got {len(parts)}", line_no
            )
        res_id, cap_str = parts
        if not res_id:
            raise InputError("RESOURCE_ID must not be empty", line_no)
        if any(ch.isspace() for ch in res_id):
            raise InputError(f"RESOURCE_ID {res_id!r} must not contain whitespace", line_no)
        if res_id not in STANDARD_RESOURCES:
            raise InputError(
                f"unknown resource ID {res_id!r}, must be in STANDARD_RESOURCES", line_no
            )
        if res_id in seen_resources:
            raise InputError(f"duplicate resource ID {res_id!r}", line_no)
        cap = _parse_int(cap_str, "CAPACITY", line_no)
        if cap != 1:
            raise InputError(f"CAPACITY must be 1 for the Library, got {cap}", line_no)
        seen_resources.add(res_id)
        declared_resources.append(ResourceSpec(res_id, cap))

    k_idx = start + 1 + r_count
    if k_idx >= len(lines):
        raise InputError("missing action count K", k_idx + 1)

    k_count = _parse_int(lines[k_idx], "K", k_idx + 1)
    if k_count < 0:
        raise InputError(f"K must be non-negative, got {k_count}", k_idx + 1)

    if len(lines) < k_idx + 1 + k_count:
        raise InputError(
            f"K is {k_count} but only {len(lines) - k_idx - 1} action row(s) follow",
            len(lines) + 1,
        )

    reader_map = {r.id: r for r in readers}
    actions: list[Action] = []
    for row_idx in range(k_count):
        idx = k_idx + 1 + row_idx
        line_no = idx + 1
        parts = [p.strip() for p in lines[idx].split(",")]
        if len(parts) != 5:
            raise InputError(
                f"expected 5 fields (ID,WORK_OFFSET,ACTION,RESOURCE_ID,UNITS), got {len(parts)}",
                line_no,
            )
        pid, offset_str, act_str, res_id, units_str = parts
        if pid not in reader_map:
            raise InputError(f"unknown reader ID {pid!r} in action", line_no)
        offset = _parse_int(offset_str, "WORK_OFFSET", line_no)
        reader = reader_map[pid]
        if not (0 <= offset <= reader.service):
            raise InputError(
                f"WORK_OFFSET must be between 0 and SERVICE ({reader.service}), got {offset}",
                line_no,
            )
        if act_str not in ("ACQUIRE", "RELEASE"):
            raise InputError(
                f"ACTION must be ACQUIRE or RELEASE, got {act_str!r}", line_no
            )
        if res_id not in seen_resources:
            raise InputError(f"undeclared resource ID {res_id!r} in action", line_no)
        units = _parse_int(units_str, "UNITS", line_no)
        if units != 1:
            raise InputError(f"UNITS must be 1, got {units}", line_no)

        actions.append(
            Action(
                reader_id=pid,
                work_offset=offset,
                action=ActionType(act_str),
                resource_id=res_id,
                units=units,
                row_index=row_idx,
            )
        )

    extra_idx = k_idx + 1 + k_count
    if extra_idx < len(lines):
        raise InputError(
            f"unexpected extra content on line {extra_idx + 1}",
            extra_idx + 1,
        )

    try:
        validate_actions(readers, declared_resources, actions)
    except InputError as exc:
        if exc.line_no is None:
            raise InputError(exc.message, start + 1) from exc
        raise

    return tuple(declared_resources), tuple(actions)
