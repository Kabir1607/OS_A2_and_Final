"""Thread-safe event logging and concurrency auditing for the Final Project.

Records fine-grained virtual-time events and thread concurrency without
altering graded simulation output.
"""

from __future__ import annotations

import threading
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import TextIO

from .models import ResourceSpec


class EventKind(str, Enum):
    """[CONTRACT 3] Who emits what:
      engine:    ARRIVE, BLOCK_MEMORY, ADMIT (detail "seats=a-b"),
                 DISPATCH (detail "librarian=k"), UNBLOCK, COMPLETE, DEADLOCK
                 (one per cycle, reader_id = smallest ID, detail = "R1->R2->R1")
      resources: ACQUIRE  reader = new holder,   resource = book
                 BLOCK    reader = requester,    resource = book, detail "held by Rx"
                 RELEASE  reader = releaser,     resource = book
                 HANDOFF  reader = NEW holder,   resource = book, detail "from Rx"
                          (always emitted straight after that book's RELEASE/ROLLBACK)
                 ROLLBACK reader = releaser,     resource = book.
                          ONE event per book released by the policy.
    """
    ARRIVE = "ARRIVE"
    BLOCK_MEMORY = "BLOCK_MEMORY"
    ADMIT = "ADMIT"
    DISPATCH = "DISPATCH"
    ACQUIRE = "ACQUIRE"
    BLOCK = "BLOCK"
    RELEASE = "RELEASE"
    HANDOFF = "HANDOFF"
    UNBLOCK = "UNBLOCK"
    ROLLBACK = "ROLLBACK"
    COMPLETE = "COMPLETE"
    DEADLOCK = "DEADLOCK"


@dataclass(frozen=True)
class TraceEvent:
    seq: int
    t: int
    kind: EventKind
    reader_id: str
    resource_id: str | None
    thread: str
    detail: str = ""


def format_event(e: TraceEvent) -> str:
    """Format one trace event into a readable line.

    e.g. '[t=3 #17 worker-1] R2 BLOCK JOURNAL (held by R1)'
    """
    base = f"[t={e.t} #{e.seq} {e.thread}] {e.reader_id} {e.kind.value}"
    if e.resource_id:
        base += f" {e.resource_id}"
    if e.detail:
        if e.detail.startswith("(") and e.detail.endswith(")"):
            base += f" {e.detail}"
        else:
            base += f" ({e.detail})"
    return base


class Tracer:
    """Thread-safe trace recorder with an optional sink."""

    def __init__(self, sink: TextIO | None = None, enabled: bool = True) -> None:
        self.sink = sink
        self.enabled = enabled
        self._lock = threading.Lock()
        self._events: list[TraceEvent] = []
        self._seq = 0

    def emit(
        self,
        t: int,
        kind: EventKind,
        reader_id: str,
        resource_id: str | None = None,
        detail: str = "",
    ) -> TraceEvent:
        """Thread-safe. Appends the event and writes format_event(e) to sink if set."""
        with self._lock:
            if self.enabled:
                self._seq += 1
                seq = self._seq
            else:
                seq = 0
            event = TraceEvent(
                seq=seq,
                t=t,
                kind=kind,
                reader_id=reader_id,
                resource_id=resource_id,
                thread=threading.current_thread().name,
                detail=detail,
            )
            if self.enabled:
                self._events.append(event)
                if self.sink is not None:
                    self.sink.write(format_event(event) + "\n")
                    self.sink.flush()
            return event

    def events(self) -> list[TraceEvent]:
        """A copy of recorded events, in seq order."""
        with self._lock:
            return list(self._events)


def audit_exclusivity(
    events: Iterable[TraceEvent],
    resources: Iterable[ResourceSpec],
) -> int:
    """Replay ownership events and return the count of exclusivity violations.

    [CONTRACT 4]: Counts instances where simultaneous holders exceed capacity,
    or where RELEASE/ROLLBACK is attempted by a non-holder.
    """
    caps = {r.id: r.capacity for r in resources}
    holders: dict[str, set[str]] = {r.id: set() for r in resources}
    violations = 0

    for event in events:
        if event.resource_id is None:
            continue
        res_id = event.resource_id
        cap = caps.get(res_id, 1)
        current = holders.setdefault(res_id, set())

        if event.kind in (EventKind.ACQUIRE, EventKind.HANDOFF):
            if event.reader_id in current:
                violations += 1
            current.add(event.reader_id)
            if len(current) > cap:
                violations += 1
        elif event.kind in (EventKind.RELEASE, EventKind.ROLLBACK):
            if event.reader_id not in current:
                violations += 1
            else:
                current.remove(event.reader_id)

    return violations
