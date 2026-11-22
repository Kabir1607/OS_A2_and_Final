"""Plain data types shared by every module (see library_sim.pyi)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Final, Mapping

# Two identical librarians serve readers in parallel.
NUM_LIBRARIANS: Final[int] = 2

# A2: the reading room has 6 contiguous seat slots.
SEAT_CAPACITY: Final[int] = 6

# Final Project: the named Library resources, each with capacity 1.
STANDARD_RESOURCES: Final[frozenset[str]] = frozenset(
    [f"OS_BOOK_{i}" for i in range(1, 11)]
    + [f"FICTION_{i}" for i in range(1, 4)]
    + ["MAG_1", "MAG_2", "REFERENCE_BOOK", "JOURNAL"]
)


class State(Enum):
    NEW = "NEW"
    BLOCKED_MEMORY = "BLOCKED_MEMORY"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED_RESOURCE = "BLOCKED_RESOURCE"
    TERMINATED = "TERMINATED"


# Legal lifecycle transitions. A1 only uses NEW -> READY -> RUNNING -> TERMINATED.
LEGAL_TRANSITIONS: Final[Mapping[State, frozenset[State]]] = MappingProxyType({
    State.NEW: frozenset({State.BLOCKED_MEMORY, State.READY}),
    State.BLOCKED_MEMORY: frozenset({State.READY}),
    State.READY: frozenset({State.RUNNING}),
    State.RUNNING: frozenset({State.BLOCKED_RESOURCE, State.TERMINATED}),
    State.BLOCKED_RESOURCE: frozenset({State.READY}),
    State.TERMINATED: frozenset(),
})


class Scheduler(str, Enum):
    FCFS = "FCFS"
    PRIORITY = "PRIORITY"


class Allocator(str, Enum):
    FIRST_FIT = "FIRST_FIT"
    BEST_FIT = "BEST_FIT"
    WORST_FIT = "WORST_FIT"


class ActionType(str, Enum):
    ACQUIRE = "ACQUIRE"
    RELEASE = "RELEASE"


@dataclass(frozen=True)
class ReaderSpec:
    """One reader row from the input. Immutable."""

    id: str
    arrival: int
    priority: int          # smaller number = higher priority
    service: int           # total service units (the "CPU burst")
    category: str          # descriptive only, never used for scheduling
    space_req: int = 1     # A2+: contiguous seats requested (A1 inputs get 1)
    table_req: int = 0     # always 0 for Library


@dataclass(frozen=True)
class ResourceSpec:
    id: str
    capacity: int


@dataclass(frozen=True)
class Action:
    reader_id: str
    work_offset: int
    action: ActionType
    resource_id: str
    units: int
    row_index: int         # 0-based position in the K section; breaks offset ties


@dataclass(frozen=True)
class SimulationInput:
    """Everything parsed from one input file."""

    quantum: int
    readers: tuple[ReaderSpec, ...]
    resources: tuple[ResourceSpec, ...] = ()
    actions: tuple[Action, ...] = ()
    has_resource_section: bool = False

    @property
    def n(self) -> int:
        return len(self.readers)

    def reader(self, reader_id: str) -> ReaderSpec:
        for spec in self.readers:
            if spec.id == reader_id:
                return spec
        raise KeyError(reader_id)

    def actions_for(self, reader_id: str) -> tuple[Action, ...]:
        """That reader's actions, stable-sorted by (work_offset, row_index)."""
        own = [a for a in self.actions if a.reader_id == reader_id]
        return tuple(sorted(own, key=lambda a: (a.work_offset, a.row_index)))


@dataclass
class Reader:
    """Mutable runtime state of one reader (engine coordinator thread only)."""

    spec: ReaderSpec
    actions: tuple[Action, ...] = ()
    state: State = State.NEW
    mem_admit: int | None = None
    start: int | None = None
    completion: int | None = None
    executed: int = 0
    next_action: int = 0
    seat_start: int | None = None
    librarian: int | None = None
    dispatched_at: int | None = None
    executed_at_dispatch: int = 0
    blocked_since: int | None = None
    resource_wait: int = 0

    @property
    def id(self) -> str:
        return self.spec.id

    def transition(self, new_state: State) -> None:
        if new_state not in LEGAL_TRANSITIONS[self.state]:
            raise AssertionError(
                f"illegal transition for {self.id}: "
                f"{self.state.value} -> {new_state.value}"
            )
        self.state = new_state


@dataclass(frozen=True)
class ReaderResult:
    """Raw timestamps of one finished reader; metrics derive everything else."""

    id: str
    arrival: int
    priority: int
    service: int
    start: int
    completion: int
    mem_admit: int
    resource_wait: int = 0
