"""
library_sim.pyi: interface contract for the Smart Library simulator
=====================================================================

This file sets out the agreed inputs and outputs of every module. It is
not runnable code. Each section below is one real module that its owner
implements as `src/library_sim/<module>.py`. If you depend on someone else's
section, code against the signatures here and don't wait for their
implementation. While their module isn't ready, write a tiny fake that
follows the same signature.

Changing a signature: tell the group first, then edit this file. This
file is the source of truth, and the code must follow it, not the other
way round.

Package layout (Python 3.10+, standard library only at runtime). The code
lives under src/ so this stub doesn't shadow the package in IDEs and type
checkers. See DEVELOPMENT.md for running the tests, including
tests/contract/test_pyi_conformance.py, which checks every module against this file.

    src/library_sim/
        __init__.py
        errors.py          Kabir
        models.py          Kabir
        scheduler.py       Kabir     (A1 FCFS / PRIORITY ready queues)
        a1.py              Kabir     (faithful A1 port + A1 CLI)
        parser.py          Kabir     (process section + top-level parse)
        metrics.py         Kabir
        output.py          Kabir
        memory.py          Aarush    (seat pool, allocators, FIFO admission, occupancy)
        engine.py          Urvashi   (virtual-clock coordinator, A2 + Final)
        cli.py             Urvashi   (A2 / Final entry points)
        resource_parser.py Samar     (R and K sections of the Final input)
        trace.py           Samar
        resources.py       Samar     (thread-safe resource manager)
        workers.py         Samar     (real worker threads)
        deadlock.py        Samar     (prevention policy, cycle detection, unsafe demo)
        experiments.py     Aarush    (A2 allocator comparison + ROLLBACK vs ORDERED comparison)

Threading rule for the whole codebase
--------------------------------------
Only ONE thread, the engine's coordinator thread, owns the virtual clock,
`Reader` objects, the ReadyQueue, the SeatPool and the AdmissionQueue.
None of those need locks. Worker threads touch shared state ONLY through
`ResourceManager` and `Tracer`, which are internally locked. Never call
`time.sleep()` for correctness, and never busy-wait.

Times are always integers (virtual time units). Ratios are floats.

Shared fakes and contract tests
-------------------------------
Every owner publishes, EARLY and before the real implementation:
  tests/fakes/fake_<module>.py           a minimal fake with the same signatures
                                         AND the same behaviour rules (e.g. the fake
                                         ResourceManager does direct handoff and
                                         writes the same trace events)
  tests/contract/test_<module>_contract.py   tests of the behaviour rules in this file
Consumers test against these shared fakes, never against private ones they
wrote themselves. The real module must pass its own contract tests, and
the fake must pass them too.

Behaviour rules between modules (the format alone isn't enough)
---------------------------------------------------------------
Search for "[CONTRACT n]" to find each rule where it applies:
  [CONTRACT 1] Advancing the action pointer after a block and wake-up      (engine, resources, workers)
  [CONTRACT 2] Blocked and woken in the same round                        (engine, workers)
  [CONTRACT 3] Who emits which trace event, and how it is shaped          (engine, resources, trace)
  [CONTRACT 4] Where CHECK,EXCLUSIVITY_VIOLATIONS comes from              (engine, resources, trace)
  [CONTRACT 5] The deadlock demo runs the REAL engine and policy code     (deadlock, engine, cli)
  [CONTRACT 6] A2 mode never imports the Final-only modules               (engine, cli, packaging)
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from typing import Final, Literal, TextIO

Mode = Literal["A1", "A2", "FINAL"]


# =============================================================================
# library_sim/errors.py  (Owner: Kabir)
# =============================================================================

class InputError(Exception):
    """Malformed or impossible input. The CLI catches it, prints
    `Error: <message>` (with a line number when known) to stderr, exits
    with status 1 and writes no output file. Never hang, never traceback."""
    message: str
    line_no: int | None          # 1-based line in the input file, if known
    def __init__(self, message: str, line_no: int | None = None) -> None: ...


class UsageError(Exception):
    """Bad command-line arguments (wrong count, unknown scheduler/allocator)."""


# =============================================================================
# library_sim/models.py  (Owner: Kabir)
# Plain data types shared by everyone. No logic beyond trivial properties.
# =============================================================================

NUM_LIBRARIANS: Final[int]       # = 2
SEAT_CAPACITY: Final[int]        # = 6
STANDARD_RESOURCES: Final[frozenset[str]]
# = {"OS_BOOK_1".."OS_BOOK_10", "FICTION_1".."FICTION_3",
#    "MAG_1", "MAG_2", "REFERENCE_BOOK", "JOURNAL"}   (17 items)


class State(Enum):
    NEW = "NEW"
    BLOCKED_MEMORY = "BLOCKED_MEMORY"
    READY = "READY"
    RUNNING = "RUNNING"
    BLOCKED_RESOURCE = "BLOCKED_RESOURCE"
    TERMINATED = "TERMINATED"


# Legal transitions. The engine asserts every transition against this table.
#   NEW -> BLOCKED_MEMORY | READY
#   BLOCKED_MEMORY -> READY
#   READY -> RUNNING
#   RUNNING -> BLOCKED_RESOURCE | TERMINATED
#   BLOCKED_RESOURCE -> READY
LEGAL_TRANSITIONS: Final[Mapping[State, frozenset[State]]]


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
    priority: int            # smaller = more important
    service: int             # B, total service units
    category: str            # descriptive only, never used for scheduling
    space_req: int = 1       # A2+: 1..6 contiguous seats (A1 inputs get 1)
    table_req: int = 0       # always 0 for Library


@dataclass(frozen=True)
class ResourceSpec:
    id: str                  # must be in STANDARD_RESOURCES
    capacity: int            # always 1 for Library


@dataclass(frozen=True)
class Action:
    reader_id: str
    work_offset: int         # 0..service; units of THIS reader's service done when the action fires
    action: ActionType
    resource_id: str
    units: int               # always 1
    row_index: int           # 0-based position in the K section; breaks ties at equal offsets


@dataclass(frozen=True)
class SimulationInput:
    """Everything parsed from one input file."""
    quantum: int                             # Q: read, validated (>= 1), unused by Library
    readers: tuple[ReaderSpec, ...]          # in FILE order (not sorted)
    resources: tuple[ResourceSpec, ...]      # () when the section is absent
    actions: tuple[Action, ...]              # () when the section is absent
    has_resource_section: bool               # True if an R line was present (even R = 0)

    @property
    def n(self) -> int: ...
    def reader(self, reader_id: str) -> ReaderSpec: ...
    def actions_for(self, reader_id: str) -> tuple[Action, ...]:
        """That reader's actions, stable-sorted by (work_offset, row_index)."""


@dataclass
class Reader:
    """Mutable runtime state of one reader. Owned and mutated ONLY by the
    engine's coordinator thread."""
    spec: ReaderSpec
    actions: tuple[Action, ...]              # = SimulationInput.actions_for(spec.id)
    state: State = ...                       # starts as State.NEW
    mem_admit: int | None = None             # M
    start: int | None = None                 # S = first dispatch (TA-approved, even if it blocks at offset 0)
    completion: int | None = None            # C
    executed: int = 0                        # service units done so far
    next_action: int = 0                     # index into `actions` of the next action not yet done.
                                             # [CONTRACT 1]: see the Simulation docstring
    seat_start: int | None = None            # first seat index while seated
    librarian: int | None = None             # 0 or 1 while RUNNING
    dispatched_at: int | None = None         # time of the current dispatch
    executed_at_dispatch: int = 0            # `executed` at the current dispatch
    blocked_since: int | None = None         # time it entered BLOCKED_RESOURCE
    resource_wait: int = 0                   # accumulated BLOCKED_RESOURCE time

    @property
    def id(self) -> str: ...
    def transition(self, new_state: State) -> None:
        """Set the state. Raises AssertionError on an illegal transition."""


@dataclass(frozen=True)
class ReaderResult:
    """Raw timestamps of one finished reader, produced by the engine
    (or the A1 port) and consumed by metrics. No derived metrics here."""
    id: str
    arrival: int             # A
    priority: int
    service: int             # B
    start: int               # S
    completion: int          # C
    mem_admit: int           # M  (A1 port: = arrival)
    resource_wait: int = 0   # 0 in A1/A2 and resource-free runs


# =============================================================================
# library_sim/scheduler.py  (Owner: Kabir)
# The A1 policies, reused unchanged by A2 and the Final.
# =============================================================================

def fcfs_key(spec: ReaderSpec) -> tuple[int, str]:
    """(arrival, id). IDs compare as plain strings, so "R10" < "R2"."""

def priority_key(spec: ReaderSpec) -> tuple[int, int, str]:
    """(priority, arrival, id)."""

def key_for(scheduler: Scheduler) -> Callable[[ReaderSpec], tuple[object, ...]]:
    """fcfs_key or priority_key."""


class ReadyQueue:
    """Readers that are READY, ordered by the scheduler's key. Heap-based.
    Not thread-safe (coordinator only). A reader returning from
    BLOCKED_RESOURCE is pushed with its ORIGINAL arrival (TA-approved),
    so insertion order never matters."""
    def __init__(self, scheduler: Scheduler) -> None: ...
    def push(self, spec: ReaderSpec) -> None:
        """Raises ValueError if that ID is already queued."""
    def pop(self) -> ReaderSpec:
        """Remove and return the best reader. Raises IndexError when empty."""
    def peek(self) -> ReaderSpec | None: ...
    def __len__(self) -> int: ...
    def __bool__(self) -> bool: ...
    def __contains__(self, reader_id: str) -> bool: ...


# =============================================================================
# library_sim/a1.py  (Owner: Kabir)
# Python port of the C++ A1. MUST reproduce tests/expected/*.out byte-for-byte.
# =============================================================================

@dataclass(frozen=True)
class A1Result:
    spec: ReaderSpec
    start: int
    completion: int


def read_a1_input(path: str) -> list[ReaderSpec]:
    """A1 format: N, Q, then N rows of ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY.
    Raises InputError."""

def fcfs(readers: Sequence[ReaderSpec]) -> list[A1Result]: ...
def priority_schedule(readers: Sequence[ReaderSpec]) -> list[A1Result]: ...

def a1_main(argv: Sequence[str]) -> int:
    """`python3 -m library_sim.a1 INPUT_FILE FCFS|PRIORITY` prints the A1
    format to stdout and returns the exit code."""


# =============================================================================
# library_sim/parser.py  (Owner: Kabir; R/K sections delegated to Samar)
# =============================================================================

def parse_text(text: str, mode: Literal["A2", "FINAL"]) -> SimulationInput:
    """Parse a whole A2 or Final input.
      * Lines 1..N+2: N, Q, N reader rows (7 fields). Rows may be in any order.
      * Trailing blank lines are ignored. Surrounding whitespace per field is stripped.
      * mode == "A2": anything after the N reader rows (other than blank lines) -> InputError.
      * mode == "FINAL": if more lines follow, call
        resource_parser.parse_resource_sections(lines, next_index, readers).
        [CONTRACT 6] Import resource_parser inside that branch only, so A2 mode
        works without the file.
    Validation (raise InputError with line_no): N >= 1, Q >= 1, exactly N rows,
    7 fields, integers where required, unique non-empty IDs without whitespace,
    ARRIVAL >= 0, PRIORITY >= 1, SERVICE >= 1, non-empty CATEGORY,
    1 <= SPACE_REQ <= 6, TABLE_REQ == 0."""

def parse_file(path: str, mode: Literal["A2", "FINAL"]) -> SimulationInput:
    """Read UTF-8 text and call parse_text. A missing or unreadable file -> InputError."""

def parse_reader_row(line: str, line_no: int) -> ReaderSpec: ...


# =============================================================================
# library_sim/resource_parser.py  (Owner: Samar)
# =============================================================================

def parse_resource_sections(
    lines: Sequence[str],
    start: int,
    readers: Sequence[ReaderSpec],
) -> tuple[tuple[ResourceSpec, ...], tuple[Action, ...]]:
    """Parse `R`, R rows of RESOURCE_ID,CAPACITY, `K`, K rows of
    ID,WORK_OFFSET,ACTION,RESOURCE_ID,UNITS, starting at lines[start]
    (0-based index). If R is present, K and both row counts must be too.
    Then calls validate_actions. Raises InputError (with line_no)."""

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
        it already holds, and nothing still held at the end."""


# =============================================================================
# library_sim/memory.py  (Owner: Aarush)
# Contiguous seat allocation, FIFO admission, occupancy statistics.
# Single-threaded (coordinator only).
# =============================================================================

FreeRun = tuple[int, int]        # (start_index, length); a maximal run of empty slots


def free_runs(slots: Sequence[str | None]) -> list[FreeRun]:
    """Maximal free runs in ascending start order. `slots[i]` is the holder ID or None."""

def choose_run(runs: Sequence[FreeRun], k: int, allocator: Allocator) -> int | None:
    """Pure function. Returns the START INDEX where k seats go, or None.
      FIRST_FIT: first run with len >= k
      BEST_FIT:  smallest run with len >= k, ties -> lowest start
      WORST_FIT: largest run with len >= k, ties -> lowest start
    Always places at the lowest index of the chosen run.
    e.g. X X . . X . : k=1 gives FF 2, BF 5, WF 2."""


class SeatPool:
    capacity: int
    allocator: Allocator
    def __init__(self, allocator: Allocator, capacity: int = 6) -> None:
        """`capacity` is configurable only so tests can use a huge pool to
        reproduce A1 timings. Graded runs always use 6."""
    def allocate(self, reader_id: str, k: int) -> int | None:
        """Place k adjacent seats using the allocator. Returns the start index,
        or None if no run fits (the pool is unchanged). ValueError if the reader
        already holds seats or k is outside 1..capacity."""
    def release(self, reader_id: str) -> FreeRun:
        """Free exactly that reader's seats. Returns (start, length).
        KeyError if it holds none. Adjacent free runs coalesce automatically."""
    def free_runs(self) -> list[FreeRun]: ...
    @property
    def occupied(self) -> int: ...
    @property
    def largest_free_run(self) -> int: ...
    def external_fragmentation(self) -> int:
        """total free - largest free run (0 when empty or full)."""
    def snapshot(self) -> tuple[str | None, ...]:
        """Owner of every slot, for traces and memory maps."""


class AdmissionQueue:
    """Strict FIFO with head-of-line blocking. Never drops, never bypasses."""
    def __init__(self, pool: SeatPool) -> None: ...
    def enqueue(self, spec: ReaderSpec) -> None:
        """The CALLER enqueues one timestamp's arrivals in ascending ID order."""
    def admit_ready(self) -> list[tuple[str, int]]:
        """Try the head repeatedly until it doesn't fit or the queue is empty.
        Returns [(reader_id, seat_start), ...] in admission order."""
    @property
    def head(self) -> str | None: ...
    def waiting_ids(self) -> list[str]: ...
    def __len__(self) -> int: ...


@dataclass(frozen=True)
class PoolStats:
    name: str                        # "SPACE"
    capacity: int                    # 6
    peak_occupied: int
    occupied_integral: int           # sum of occupied * interval over [min A, max C]
    max_ext_frag: int
    start_time: int                  # min A
    end_time: int                    # max C

    @property
    def utilization_pct(self) -> float:
        """occupied_integral / (capacity * (end_time - start_time)) * 100."""


class OccupancyTracker:
    def __init__(self, capacity: int) -> None: ...
    def sample(self, t: int, pool: SeatPool) -> None:
        """Called ONCE per processed timestamp, after ALL processing at t
        (TA-approved). t must be non-decreasing. The occupancy recorded at t
        holds until the next sample. Updates peak and max F_ext."""
    def finish(self, end_time: int) -> PoolStats: ...


# =============================================================================
# library_sim/trace.py  (Owner: Samar)
# Thread-safe, human-readable event log. Goes to stderr or a --trace file,
# NEVER into the graded output file.
# =============================================================================

class EventKind(str, Enum):
    """[CONTRACT 3] Who emits what (reader_id / resource_id / detail):
      engine    ARRIVE, BLOCK_MEMORY, ADMIT (detail "seats=a-b"),
                DISPATCH (detail "librarian=k"), UNBLOCK, COMPLETE, DEADLOCK
                (one per cycle, reader_id = smallest ID, detail = "R1->R2->R1")
      resources ACQUIRE  reader = new holder,   resource = book
                BLOCK    reader = requester,    resource = book, detail "held by Rx"
                RELEASE  reader = releaser,     resource = book
                HANDOFF  reader = NEW holder,   resource = book, detail "from Rx"
                         (always emitted straight after that book's RELEASE/ROLLBACK)
                ROLLBACK reader = releaser,     resource = book.
                         ONE event per book released by the policy.
    Events are emitted INSIDE the ResourceManager's critical section, so
    their seq order is consistent with the real order of ownership changes.
    The holder count audit_exclusivity replays:
    ACQUIRE +1 and HANDOFF +1 for the reader; RELEASE -1 and ROLLBACK -1 for the reader."""
    ARRIVE = "ARRIVE"
    BLOCK_MEMORY = "BLOCK_MEMORY"
    ADMIT = "ADMIT"
    DISPATCH = "DISPATCH"
    ACQUIRE = "ACQUIRE"          # granted
    BLOCK = "BLOCK"              # acquire could not be granted
    RELEASE = "RELEASE"
    HANDOFF = "HANDOFF"          # a release handed the resource directly to a waiter
    UNBLOCK = "UNBLOCK"          # waiter now READY
    ROLLBACK = "ROLLBACK"        # prevention policy released held resources
    COMPLETE = "COMPLETE"
    DEADLOCK = "DEADLOCK"


@dataclass(frozen=True)
class TraceEvent:
    seq: int                     # global order the events were logged in (under the lock)
    t: int                       # virtual time
    kind: EventKind
    reader_id: str
    resource_id: str | None
    thread: str                  # threading.current_thread().name, shows real concurrency
    detail: str = ""


class Tracer:
    def __init__(self, sink: TextIO | None = None, enabled: bool = True) -> None: ...
    def emit(self, t: int, kind: EventKind, reader_id: str,
             resource_id: str | None = None, detail: str = "") -> TraceEvent:
        """Thread-safe. Appends the event and writes format_event(e) to sink if set."""
    def events(self) -> list[TraceEvent]:
        """A copy, in seq order."""


def format_event(e: TraceEvent) -> str:
    """e.g. '[t=3 #17 worker-1] R2 BLOCK JOURNAL (held by R1)'"""

def audit_exclusivity(events: Iterable[TraceEvent],
                      resources: Iterable[ResourceSpec]) -> int:
    """Replays ACQUIRE/HANDOFF/RELEASE/ROLLBACK independently of the
    ResourceManager and counts the moments a resource had more holders
    than its capacity. Also counts RELEASE/ROLLBACK by a non-holder.
    [CONTRACT 4]: the engine reports
    max(ResourceManager.exclusivity_violations(), audit_exclusivity(...))
    so neither count can hide a violation the other one saw."""


# =============================================================================
# library_sim/deadlock.py  (Owner: Samar)
# =============================================================================

class PreventionPolicy(str, Enum):
    """BOTH ROLLBACK and ORDERED are fully implemented and selectable with
    --policy. Both must accept ANY valid input order (never reject an input
    because of its acquisition order), so COMPLETED_COUNT == N always.

    NONE: unsafe. A blocked reader simply waits while holding. Only used by
    the bounded deadlock demo (and to show the cycle in experiments).

    ROLLBACK (breaks HOLD AND WAIT):
      ACQUIRE X is free             -> grant.
      ACQUIRE X is busy, holds none -> wait for {X}.
      ACQUIRE X is busy, holds H    -> release ALL of H now (ROLLBACK events,
                                       handed to waiters), then wait for H + {X}.
      A waiting set is granted ATOMICALLY, only when every member is free.
      A reader therefore never waits while holding anything.

    ORDERED (breaks CIRCULAR WAIT):
      Global order = resource_rank() (string order of resource IDs).
      Invariant: a reader only ever WAITS for a resource ranked above
      everything it holds. Grants of free resources are allowed in any
      order: they create no wait-for edge.
      ACQUIRE X is free                         -> grant (even out of order).
      ACQUIRE X is busy, all held rank < X      -> wait for X, keeping holdings.
      ACQUIRE X is busy, some held rank > X     -> release only the held ones
                                                   ranked above X (ROLLBACK
                                                   events), then re-acquire
                                                   X + those in ascending rank,
                                                   one at a time, waiting at each
                                                   step while keeping the lower ones.
      The reader is woken only once it holds the whole sequence.

    Either way, a woken reader already owns everything its blocked ACQUIRE
    needed (plus anything that was rolled back), so the engine needs no
    policy-specific code. The work offset does not rewind after a
    rollback: a documented modelling simplification."""
    NONE = "NONE"
    ROLLBACK = "ROLLBACK"
    ORDERED = "ORDERED"


DEFAULT_POLICY: Final[PreventionPolicy]
# Set from the policy comparison (experiments.compare_policies) before the
# Final zip is built. Until then it is ROLLBACK, so code has a value to run with.


def resource_rank(resource_id: str, declared: Sequence[str]) -> int:
    """Position of resource_id in sorted(declared). Used by ORDERED. Plain
    string order, so "OS_BOOK_10" < "OS_BOOK_2"; that is fine, any total
    order works."""


@dataclass(frozen=True)
class PolicyStats:
    """Counters for the policy comparison. Kept OUT of the graded output
    file, and shown with --stats or in experiments."""
    policy: PreventionPolicy
    rollbacks: int                   # times the policy forced a reader to give up held resources
    resources_rolled_back: int       # total resources released by the policy (not by the input)
    reacquisitions: int              # grants that gave back a rolled-back resource
    out_of_order_requests: int       # ACQUIREs whose resource ranks below something already held
    held_while_waiting: int          # wait events where the waiter held >= 1 resource (0 under ROLLBACK)


def find_cycles(wait_for: Mapping[str, Iterable[str]]) -> list[list[str]]:
    """Wait-for graph reader -> readers it waits on. Returns each elementary
    cycle once, e.g. [["R1", "R2"]]. Deterministic: rotated to start at the smallest ID."""


UNSAFE_DEMO_INPUT: Final[str]
# Path of the bundled unsafe workload: inputs/deadlock_unsafe.txt, the
# spec's section 8.1 Library workload with R2's acquisition order reversed
# (R1: REFERENCE_BOOK then JOURNAL; R2: JOURNAL then REFERENCE_BOOK).


@dataclass(frozen=True)
class DemoReport:
    policy: PreventionPolicy
    deadlocked: bool             # True if the engine found a wait-for cycle with no progress possible
    cycle: tuple[str, ...]       # e.g. ("R1", "R2"); () if none
    completed: tuple[str, ...]   # readers that finished
    result: SimulationResult     # the full engine result (metrics, checks, policy_stats)
    events: tuple[TraceEvent, ...]


def run_unsafe_demo(policies: Sequence[PreventionPolicy] = ...,  # (NONE, ROLLBACK, ORDERED)
                    input_path: str = ...,                       # UNSAFE_DEMO_INPUT
                    scheduler: Scheduler = ...,                  # FCFS
                    allocator: Allocator = ...,                  # FIRST_FIT
                    tracer: Tracer | None = None) -> list[DemoReport]:
    """[CONTRACT 5] The demo runs the REAL engine (Simulation in FINAL mode),
    with its real ResourceManager, WorkerPool and policy code, once per
    policy. No demo-only locking code, so the policy shown fixing the
    unsafe case is exactly the one used in normal runs.

    Why it is bounded with no timeout: at t=0 both readers are dispatched
    and their first ACQUIREs run concurrently on worker threads. At t=1
    each requests the other's book.
      NONE:     both BLOCKED while holding -> no RUNNING reader, no future
                event -> the engine stops (Simulation U5 rule), find_cycles
                reports ("R1", "R2"), CHECK,UNRESOLVED_DEADLOCKS = 1.
      ROLLBACK: whichever blocks while holding gives up its book (the race
                decides which), and both finish.
      ORDERED:  JOURNAL < REFERENCE_BOOK, so R2 waits in order keeping
                JOURNAL. R1's request is out of order, so R1 releases
                REFERENCE_BOOK and re-acquires JOURNAL then REFERENCE_BOOK.
                Both finish."""


def run_blocking_demo(timeout_s: float = 2.0, tracer: Tracer | None = None) -> DemoReport:
    """OPTIONAL extra, not required by the spec: the same circular wait
    using real thread blocking. A threading.Barrier makes both threads hold
    their first book before asking for the second, and waits use
    Condition.wait(timeout=...), so it always returns. Must call the same
    ResourceManager for grants and releases (it only adds a blocking wait
    around acquire()). `result` is a minimal SimulationResult."""


# =============================================================================
# library_sim/resources.py  (Owner: Samar)
# The ONLY shared mutable state touched by worker threads.
# =============================================================================

class AcquireStatus(str, Enum):
    GRANTED = "GRANTED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class AcquireOutcome:
    status: AcquireStatus
    resource_id: str
    rolled_back: tuple[str, ...] = ()   # resources the policy made this reader give up (ROLLBACK)
    woken: tuple[str, ...] = ()         # readers whose wait was satisfied by that rollback


@dataclass(frozen=True)
class ReleaseOutcome:
    resource_id: str
    woken: tuple[str, ...] = ()         # readers that now OWN everything they waited for


@dataclass(frozen=True)
class ResourceStats:
    resource_id: str
    capacity: int
    max_simultaneous_holders: int
    acquisitions: int                   # successful grants, including handoffs and re-grants
    wait_events: int                    # times an acquire returned BLOCKED


class ResourceManager:
    """One threading.Lock (or a lock per resource plus an ordered global
    lock, your choice) protects all ownership and counters. Check and
    update happen inside the SAME critical section.

    Virtual-time blocking: acquire() never parks the worker thread waiting
    for virtual time. It returns BLOCKED and records the reader as a
    waiter. On release, the resource is handed DIRECTLY to the first
    eligible waiter while the lock is still held (TA-approved: no lost
    wake-ups, nobody can steal it). "Eligible" depends on the policy:
    under ROLLBACK, the first FIFO waiter whose WHOLE set is now free;
    under ORDERED, the first FIFO waiter for that resource, which then
    continues its ascending sequence inside the same critical section.
    A woken reader already owns everything it was waiting for when the
    engine re-dispatches it. The policy rules are in the PreventionPolicy
    docstring."""
    def __init__(self, resources: Iterable[ResourceSpec],
                 policy: PreventionPolicy, tracer: Tracer) -> None: ...
    def acquire(self, reader_id: str, resource_id: str, t: int) -> AcquireOutcome:
        """RuntimeError if reader_id already holds resource_id or is already
        waiting (catches engine bugs such as re-running an ACQUIRE after a
        wake-up, [CONTRACT 1]). Emits trace events inside the lock [CONTRACT 3]."""
    def release(self, reader_id: str, resource_id: str, t: int) -> ReleaseOutcome:
        """RuntimeError on a double release or a release by a non-holder."""
    def held_by(self, reader_id: str) -> frozenset[str]: ...
    def is_waiting(self, reader_id: str) -> bool: ...
    def wait_for_graph(self) -> dict[str, set[str]]: ...
    def stats(self) -> tuple[ResourceStats, ...]:
        """Sorted by resource_id."""
    def exclusivity_violations(self) -> int:
        """Counted inside the lock. Must be 0. Cross-checked by trace.audit_exclusivity."""
    def nothing_held(self) -> bool:
        """True when no resource has a holder and there are no waiters (end-of-run conservation check)."""
    def policy_stats(self) -> PolicyStats: ...


# =============================================================================
# library_sim/workers.py  (Owner: Samar)
# Real OS threads (threading / concurrent.futures.ThreadPoolExecutor).
# =============================================================================

@dataclass(frozen=True)
class ActionBatch:
    """The actions ONE reader must perform at virtual time t: all of its
    actions at its current offset, in row order. Different readers' batches
    run concurrently. Within a batch they run sequentially, stopping at the
    first BLOCKED acquire."""
    reader_id: str
    t: int
    actions: tuple[Action, ...]


@dataclass(frozen=True)
class BatchResult:
    reader_id: str
    done: int                    # how many actions of the batch completed (granted or released)
    blocked: bool                # True if actions[done] was an ACQUIRE that returned BLOCKED.
                                 # actions[done] is NOT counted in `done` [CONTRACT 1]
    woken: tuple[str, ...]       # union of readers woken by this batch's releases/rollbacks
    thread: str                  # name of the worker thread that ran it


class WorkerPool:
    def __init__(self, manager: ResourceManager, num_workers: int = 2) -> None: ...
    def run_batches(self, batches: Sequence[ActionBatch]) -> list[BatchResult]:
        """Submit every batch to the worker threads, wait for all to finish
        (futures/join, never sleep) and return results in the SAME order as
        `batches`. Exceptions in workers re-raise here."""
    def shutdown(self) -> None: ...
    def __enter__(self) -> WorkerPool: ...
    def __exit__(self, *exc: object) -> None: ...


# =============================================================================
# library_sim/engine.py  (Owner: Urvashi)
# The virtual-clock coordinator: one discrete-event loop for A2 and the Final.
# =============================================================================

@dataclass(frozen=True)
class CheckStats:
    exclusivity_violations: int  # [CONTRACT 4] max(manager count, trace audit)
    unresolved_deadlocks: int    # number of wait-for cycles found when no progress was possible
    completed_count: int


@dataclass(frozen=True)
class SimulationResult:
    readers: tuple[ReaderResult, ...]        # COMPLETED readers only, sorted by ID
    incomplete: tuple[str, ...]              # IDs that never terminated (empty in a correct run)
    pool: PoolStats
    resources: tuple[ResourceStats, ...]     # () in A2 mode and when no resources are declared
    checks: CheckStats | None                # None in A2 mode
    deadlock_cycles: tuple[tuple[str, ...], ...]
    trace: tuple[TraceEvent, ...]
    policy_stats: PolicyStats | None         # None in A2 mode
    wall_time_s: float                       # real elapsed time of run(), for sync-overhead comparison


class Simulation:
    """Event order at each timestamp t (TA-approved). Repeat steps 1-7 until
    nothing changes at t, then OccupancyTracker.sample(t), then jump to the
    next event time:
      1. Resource actions due at t for RUNNING readers (WorkerPool, concurrent),
         including RELEASEs at offset == SERVICE.
      2. Completions at t (ascending ID): free the librarian, SeatPool.release.
      3. Arrivals at t (ascending ID) -> AdmissionQueue.enqueue.
      4. AdmissionQueue.admit_ready() -> READY (M = t).
      5. Readers woken in step 1 -> READY (resource_wait += t - blocked_since).
      6. Fill idle librarians, lower-numbered first, from ReadyQueue (S = t on first dispatch).
      7. Newly dispatched readers whose next action is at their current offset
         perform it now. If one blocks, free its librarian and go back to 6.
    In A2 mode and resource-free Final runs, steps 1, 5 and 7 are no-ops, so
    the result equals A2 exactly.
    Next event time = min(next arrival, running completions, running
    readers' next action time = dispatched_at + (offset - executed_at_dispatch)).
    If no event remains but readers are unfinished, stop and report the cycles
    (never hang).

    [CONTRACT 1] Advancing the action pointer:
      * After a BatchResult: reader.next_action += result.done.
      * If result.blocked: actions[next_action] is the ACQUIRE that blocked.
        Do NOT advance past it yet.
      * When the reader is woken (it appears in some `woken` tuple), it
        already OWNS that book, so reader.next_action += 1 at wake time.
        The ACQUIRE is never re-run. Re-running it is a double acquire, and
        ResourceManager raises RuntimeError.
      * Rolled-back books are re-owned on wake, and the reader's action list
        does not change.

    [CONTRACT 2] Handling one round of BatchResults, in this order:
      a. Apply every result's `done` and `blocked` first: each blocked reader
         -> BLOCKED_RESOURCE, blocked_since = t, its librarian freed.
      b. Then process the union of all `woken` tuples. Each woken reader must
         now be BLOCKED_RESOURCE (assert it), and goes -> READY with
         resource_wait += t - blocked_since. A reader blocked and woken in
         the same round therefore ends READY with resource_wait += 0.
      Woken readers are queued for step 5 at this t, never dropped.

    [CONTRACT 3] The engine emits ARRIVE, BLOCK_MEMORY, ADMIT, DISPATCH,
    UNBLOCK, COMPLETE and DEADLOCK. ResourceManager emits the rest.

    [CONTRACT 6] engine.py imports resources, workers, deadlock and
    trace only inside FINAL-mode code paths, or under typing.TYPE_CHECKING.
    In A2 mode Simulation must run with those files ABSENT, so the A2 zip
    can ship without them. `policy=None` means DEFAULT_POLICY, resolved
    lazily in FINAL mode, and is ignored in A2 mode."""
    def __init__(
        self,
        inp: SimulationInput,
        scheduler: Scheduler,
        allocator: Allocator,
        *,
        mode: Literal["A2", "FINAL"],
        policy: PreventionPolicy | None = None,
        tracer: Tracer | None = None,
        pool_capacity: int = 6,
        num_librarians: int = 2,
        num_workers: int = 2,
    ) -> None: ...
    def run(self) -> SimulationResult: ...


def simulate(inp: SimulationInput, scheduler: Scheduler, allocator: Allocator,
             mode: Literal["A2", "FINAL"], **kwargs: object) -> SimulationResult: ...


# =============================================================================
# library_sim/metrics.py  (Owner: Kabir)
# Pure functions: raw timestamps in, numbers out.
# =============================================================================

@dataclass(frozen=True)
class ProcessMetrics:
    id: str
    arrival: int
    priority: int
    service: int
    start: int
    completion: int
    waiting: int                 # C - A - B
    turnaround: int              # C - A
    response: int                # S - A
    mem_admit: int               # M
    mem_wait: int                # M - A
    ready_wait: int              # waiting - mem_wait - resource_wait
    resource_wait: int


@dataclass(frozen=True)
class SummaryMetrics:
    average_waiting: float
    average_turnaround: float
    average_response: float
    throughput: float                        # N / E, E = max C - min A
    service_utilization_pct: float           # sum B / (2E) * 100
    average_memory_wait: float
    completed_count: int
    blocked_for_memory_count: int            # readers with M > A


def compute_process_metrics(results: Iterable[ReaderResult]) -> list[ProcessMetrics]:
    """Sorted by ID (plain string order). Asserts waiting == mem_wait + ready_wait + resource_wait."""

def compute_summary(metrics: Sequence[ProcessMetrics],
                    num_librarians: int = 2) -> SummaryMetrics: ...


# =============================================================================
# library_sim/output.py  (Owner: Kabir)
# Graded formats. No header rows, no prose, '\n' line endings, UTF-8.
# =============================================================================

def fmt_decimal(x: float) -> str:
    """Always 4 decimal places: 3.6667, 75.0000 (TA-approved)."""

def format_a1(metrics: Sequence[ProcessMetrics], summary: SummaryMetrics) -> str:
    """The exact C++ A1 format (header row, SUMMARY block, 6 decimals)."""

def format_a2(metrics: Sequence[ProcessMetrics], summary: SummaryMetrics,
              pool: PoolStats) -> str:
    """PROCESS,ID,ARRIVAL,PRIORITY,SERVICE,START,COMPLETION,WAITING,TURNAROUND,RESPONSE,MEM_ADMIT,MEM_WAIT,READY_WAIT
    then the 8 SUMMARY lines in spec order, then
    POOL,SPACE,6,PEAK_OCCUPIED,UTILIZATION_PCT,MAX_EXT_FRAG_SLOTS"""

def format_final(metrics: Sequence[ProcessMetrics], summary: SummaryMetrics,
                 pool: PoolStats, resources: Sequence[ResourceStats],
                 checks: CheckStats) -> str:
    """The A2 lines with ,RESOURCE_WAIT appended to each PROCESS line, then
    RESOURCE,ID,CAPACITY,MAX_SIMULTANEOUS_HOLDERS,ACQUISITIONS,WAIT_EVENTS (sorted by ID),
    then CHECK,EXCLUSIVITY_VIOLATIONS / CHECK,UNRESOLVED_DEADLOCKS / CHECK,COMPLETED_COUNT.
    CHECK lines are emitted even for resource-free inputs (TA-approved)."""

def write_output(path: str, text: str) -> None: ...


# =============================================================================
# library_sim/experiments.py  (Owner: Aarush; policy workloads + analysis: Samar)
# Comparison harness. Never part of graded output. Run with
#   python3 -m library_sim.experiments allocators INPUT [--md OUT.md]
#   python3 -m library_sim.experiments policies INPUT... [--repeats 30] [--md OUT.md]
# [CONTRACT 6] Ships in BOTH zips (the A2 spec asks for a repeatable comparison
# script). Import deadlock/resources only inside the policy functions, so
# `allocators` works in the A2 zip without the Final-only modules.
# =============================================================================

@dataclass(frozen=True)
class RunSummary:
    input_name: str
    scheduler: Scheduler
    allocator: Allocator
    policy: PreventionPolicy | None          # None for A2-mode runs
    summary: SummaryMetrics
    pool: PoolStats
    total_resource_wait: int                 # sum of RESOURCE_WAIT
    max_resource_wait: int                   # worst single reader (fairness / starvation)
    resources: tuple[ResourceStats, ...]
    policy_stats: PolicyStats | None
    checks: CheckStats | None
    wall_time_s: float


def run_once(inp: SimulationInput, input_name: str, scheduler: Scheduler,
             allocator: Allocator, mode: Literal["A2", "FINAL"],
             policy: PreventionPolicy | None = None) -> RunSummary: ...


def compare_allocators(inp: SimulationInput, input_name: str) -> list[RunSummary]:
    """A2 mode, 2 schedulers x 3 allocators = 6 runs (deterministic, one run each)."""


@dataclass(frozen=True)
class Spread:
    mean: float
    min: float
    max: float


@dataclass(frozen=True)
class PolicyComparisonRow:
    """One (input, scheduler, policy) cell aggregated over `runs` repeats.
    Repeats are needed because racing threads can pick different winners,
    which changes the virtual-time results."""
    input_name: str
    scheduler: Scheduler
    allocator: Allocator
    policy: PreventionPolicy
    runs: int
    all_completed: bool                      # COMPLETED_COUNT == N in every run
    all_safe: bool                           # 0 violations and 0 unresolved deadlocks in every run
    average_waiting: Spread
    average_turnaround: Spread
    throughput: Spread
    service_utilization_pct: Spread
    total_resource_wait: Spread
    max_resource_wait: Spread
    acquisitions: Spread                     # summed over resources: churn
    wait_events: Spread
    rollbacks: Spread
    resources_rolled_back: Spread
    held_while_waiting: Spread
    wall_time_s: Spread                      # synchronization overhead (real time)


def compare_policies(
    inputs: Sequence[tuple[str, SimulationInput]],
    policies: Sequence[PreventionPolicy] = ...,   # (ROLLBACK, ORDERED)
    schedulers: Sequence[Scheduler] = ...,        # (FCFS, PRIORITY)
    allocator: Allocator = ...,                   # FIRST_FIT
    repeats: int = 30,
) -> list[PolicyComparisonRow]: ...


def better_policy_by_metric(rows: Sequence[PolicyComparisonRow]
                            ) -> dict[tuple[str, Scheduler, str], PreventionPolicy | None]:
    """For each (input, scheduler, metric name): the policy with the better
    mean (lower is better except throughput/utilization), or None if the
    two differ by less than 1e-3. Feeds the README "which policy wins where" table."""


def format_markdown(rows: Sequence[RunSummary] | Sequence[PolicyComparisonRow]) -> str: ...


# =============================================================================
# library_sim/cli.py  (Owner: Urvashi)
# =============================================================================

def a2_main(argv: Sequence[str]) -> int:
    """`python3 main.py INPUT_FILE FCFS|PRIORITY FIRST_FIT|BEST_FIT|WORST_FIT OUTPUT_FILE`
    Exit codes: 0 ok, 1 usage/input error (message on stderr, no output file).
    [CONTRACT 6] Imports only the A2 modules (errors, models, scheduler,
    parser, memory, engine, metrics, output). No --policy, --trace or --stats."""

def final_main(argv: Sequence[str]) -> int:
    """`python3 main.py INPUT_FILE SCHEDULER ALLOCATOR OUTPUT_FILE
         [--trace FILE|-] [--policy ROLLBACK|ORDERED] [--stats] [--quiet]`
       (--stats prints PolicyStats + wall time to stderr, never into OUTPUT_FILE)
       `python3 main.py --demo-deadlock [INPUT_FILE] [--policy NONE|ROLLBACK|ORDERED]`
         (default: UNSAFE_DEMO_INPUT under all three policies, side by side, via
         deadlock.run_unsafe_demo [CONTRACT 5])
    Prevention is ON by default. Exit codes: 0 ok, 1 usage/input error,
    2 run finished with incomplete readers or deadlocks (clearly reported on stderr)."""
