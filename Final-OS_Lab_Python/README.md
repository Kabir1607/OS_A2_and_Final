# Smart Library — Final Project (CS-3710)

**Concurrency and integrated simulation.** Group: Kabir, Urvashi, Aarush, Samar.
Scenario: **Smart Library**. Language: Python 3.10+, standard library only.
No compilation, installation, virtual environment or GUI is needed.

This program simulates a library from start to finish. A reader arrives,
waits for a block of adjacent reading seats, waits for one of two
librarians, and borrows and returns named books and journals while being
served. It then leaves. The simulation answers the project's three questions:

| Question | Stage | OS concept | Library meaning |
|---|---|---|---|
| Who should be served next? | A1 | Process scheduling | FCFS / PRIORITY over two librarians |
| Where can the reader be allocated? | A2 | Contiguous memory allocation | First/Best/Worst Fit over six adjacent seats, FIFO admission |
| How can readers safely share limited books? | Final | Threads, synchronization, deadlock prevention | Real worker threads acquire and release named books under a lock, with deadlock prevention |

The simulation clock is virtual, but the book operations run on real
operating-system threads. They are protected by real locks, as the spec
requires (§4.1).

---

## Contents

1. [Quick start](#1-quick-start)
2. [Scenario and OS abstractions](#2-scenario-and-os-abstractions)
3. [Integrated architecture](#3-integrated-architecture)
4. [Input, command line and output](#4-input-command-line-and-output)
5. [Retained A1 and A2 algorithms](#5-retained-a1-and-a2-algorithms)
6. [Metrics](#6-metrics)
7. [Virtual time and real threads](#7-virtual-time-and-real-threads)
8. [Worker threads and synchronization](#8-worker-threads-and-synchronization)
9. [Resource ownership, blocking and wake-up](#9-resource-ownership-blocking-and-wake-up)
10. [Deadlock: conditions, demonstration and prevention](#10-deadlock-conditions-demonstration-and-prevention)
11. [Resource-event trace](#11-resource-event-trace)
12. [Final challenge evidence](#12-final-challenge-evidence)
13. [Observed comparison results](#13-observed-comparison-results)
14. [Trade-offs](#14-trade-offs)
15. [Testing](#15-testing)
16. [Assumptions](#16-assumptions)
17. [Limitations](#17-limitations)
18. [Optional features](#18-optional-features)
19. [Requirements checklist](#19-requirements-checklist)
20. [Code layout and ownership](#20-code-layout-and-ownership)

---

## 1. Quick start

Unzip the Final archive and run these commands from the unzipped folder. A
plain `python3` (3.10 or newer) is enough.

```bash
# (i) Baseline with no shared resources: the same numbers as A2, plus RESOURCE_WAIT=0 and CHECK lines
python3 main.py inputs/a2/comparison.txt FCFS FIRST_FIT baseline.txt

# (ii) Concurrency workload with real book contention (the spec's sample), with trace and statistics
python3 main.py inputs/spec_sample.txt FCFS FIRST_FIT output.txt --trace - --stats

# (iii) Bounded deadlock demo: NONE deadlocks, ROLLBACK and ORDERED complete
python3 main.py --demo-deadlock

# Comparisons and tests
python3 -m library_sim.experiments allocators inputs/a2/comparison.txt --md allocator-report.md
python3 -m library_sim.experiments policies inputs/policy/*.txt --repeats 30 --md policy-report.md
python3 -m unittest discover -s tests -t . -v
```

**From the source repository** (not the zip), run the same commands from
the repository root:

- Put `src` on the path for the package: `PYTHONPATH=src python3 -m library_sim.experiments ...`
- Call the entry point directly:

  ```bash
  PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import final_main; raise SystemExit(final_main(sys.argv[1:]))' inputs/spec_sample.txt FCFS FIRST_FIT output.txt
  ```
- `python3 build_packages.py` rebuilds `dist/a2.zip` and `dist/final.zip`.
  It unzips each into a clean folder and checks it there: the test suite,
  all six scheduler × allocator combinations and the experiments, plus the
  deadlock demo for Final.

---

## 2. Scenario and OS abstractions

| Library | OS abstraction |
|---|---|
| Reader (`R1`, `R2`, …) | Process |
| Two identical librarians | Two execution units (CPUs). When both are idle, the lower-numbered one is used first |
| Service time | CPU burst, in integer virtual time units |
| Six indexed reading seats `SPACE[0..5]` | Fixed contiguous memory pool |
| Request for `SPACE_REQ` adjacent seats | Contiguous memory allocation |
| Queue for seats | `BLOCKED_MEMORY` with FIFO memory admission |
| Seated reader waiting for a librarian | `READY` queue |
| Named books and journals | Shared resources with exclusive ownership (capacity 1 each) |
| Reader waiting for a book | `BLOCKED_RESOURCE` |
| Returning seats and books on completion | Termination and deallocation |

**Shared resource inventory** (spec §3). Each item is a separate physical
copy with capacity 1. An input may declare any subset of:

- `OS_BOOK_1` … `OS_BOOK_10`
- `FICTION_1` … `FICTION_3`
- `MAG_1`, `MAG_2`
- `REFERENCE_BOOK`
- `JOURNAL`

Different copies, such as `OS_BOOK_3` and `OS_BOOK_7`, can be held by
different readers at the same time.

**Reader lifecycle** (every change goes through `Reader.transition`, which
rejects illegal moves):

```text
NEW ──arrive──▶ BLOCKED_MEMORY ──seats granted──▶ READY ──dispatch──▶ RUNNING ──finish──▶ TERMINATED
                                                    ▲                    │
                                                    └──book granted── BLOCKED_RESOURCE ◀──ACQUIRE refused
```

- A reader becomes READY only after its whole seat block is granted.
- It keeps its seats while READY, RUNNING and BLOCKED_RESOURCE, and frees
  them only when it completes.
- A reader blocked on a book gives up its librarian, keeps its seats, and
  must be scheduled again later.

---

## 3. Integrated architecture

```text
                    input file
                        │
             parser.py + resource_parser.py         (validation, line-numbered errors)
                        │
                        ▼
 ┌──────────────── engine.py: coordinator (main thread) ────────────────┐
 │ owns the virtual clock, Reader objects, the READY queue, the FIFO    │
 │ admission queue and the SeatPool                                     │
 │                                                                      │
 │   memory.py      SeatPool (First/Best/Worst Fit), AdmissionQueue     │
 │                  (strict FIFO), OccupancyTracker                     │
 │   scheduler.py   ReadyQueue: FCFS or PRIORITY key, two librarians    │
 │                                                                      │
 │   at each timestamp: the action batches that are due ───┐            │
 └─────────────────────────────────────────────────────────┼────────────┘
                                                           ▼
                      workers.py: WorkerPool (2 real threads: worker-1, worker-2)
                                                           │  ACQUIRE / RELEASE
                                                           ▼
                      resources.py: ResourceManager (one threading.Lock)
                      ownership, waiters, handoff, ROLLBACK / ORDERED / NONE policy
                                                           │
                      trace.py: Tracer (its own lock) ◀────┘  events from both sides
                                                           │
 metrics.py ─▶ output.py ─▶ graded output file      deadlock.py: ranks, cycle check, demos
```

| Module | Responsibility |
|---|---|
| `models.py`, `errors.py` | Shared types, the lifecycle table, constants (2 librarians, 6 seats, 17 resource names), `InputError` and `UsageError` |
| `parser.py` | N, Q and the reader rows, with full A2 validation. In Final mode, hands any extra sections to `resource_parser.py` |
| `resource_parser.py` | The R and K sections: inventory names, capacity 1, units 1, known readers and resources, offsets 0..SERVICE in non-decreasing order, balanced ownership |
| `scheduler.py` | `ReadyQueue`, a heap keyed by `(arrival, id)` for FCFS or `(priority, arrival, id)` for PRIORITY |
| `memory.py` | `SeatPool` (contiguous placement, free, fragmentation), `AdmissionQueue` (strict FIFO), `OccupancyTracker` (time-weighted utilization) |
| `engine.py` | Discrete-event coordinator. Runs the event order, dispatches librarians, applies worker results, records timestamps, checks invariants at the end of each run |
| `workers.py` | `WorkerPool` on `ThreadPoolExecutor`; runs one action batch per reader that is due; overlap evidence |
| `resources.py` | `ResourceManager`: locked ownership, waiter queues, direct handoff, the three policies, counters, wait-for graph |
| `deadlock.py` | `PreventionPolicy`, resource ranks, `find_cycles`, the bounded unsafe demo (`run_unsafe_demo`), an optional thread-level blocking demo |
| `trace.py` | Thread-safe event log, plus an ownership replay that counts exclusivity violations independently |
| `metrics.py`, `output.py` | Per-reader metrics with consistency checks, the summary, and the exact output format with 4 decimal places |
| `cli.py`, `main.py` | Command line, options, exit codes |
| `experiments.py` | Allocator and policy comparisons (not graded output) |

The code keeps scheduling, memory admission, resource synchronization and
reporting separate (spec §11). Only the coordinator thread touches readers,
queues and seats. Worker threads touch shared state only through
`ResourceManager` and `Tracer`, and both are lock-protected.

### Event order within one timestamp

The coordinator jumps straight to the next timestamp where something
happens: an arrival, a completion or a due resource action. It never
sleeps. At timestamp *t* it repeats these steps until nothing changes:

1. **Resource actions.** Each running reader that has reached its next
   action offset gets one batch, covering all its actions at that offset in
   input-row order. The batches for different readers run concurrently on
   worker threads. Results are applied once every batch has finished. A
   refused ACQUIRE moves its reader to BLOCKED_RESOURCE and frees its
   librarian. Readers whose books were handed over become READY.
2. **Completions**, in ascending ID order: free the librarian and the seats.
   A RELEASE at offset SERVICE runs in step 1, before this step.
3. **Arrivals**, in ascending ID order, join the FIFO admission queue.
4. **Memory admission** starts at the queue head and stops at the first
   reader that does not fit.
5. **Dispatch.** Idle librarians are filled from the READY queue, the
   lower-numbered librarian first. A newly dispatched reader whose next
   action is due now performs it in the next pass of step 1.

Seat occupancy and fragmentation are recorded once, after *t* is finished.
Without resource actions, step 1 never does anything, so the order reduces
exactly to A2's (completions → arrivals → admission → dispatch). That is
why resource-free Final runs reproduce A2 exactly.

---

## 4. Input, command line and output

### Input (spec §8)

The first N + 2 lines are exactly the A2 input. The resource and action
sections are optional.

```text
N
Q
ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY,SPACE_REQ,TABLE_REQ      × N
R
RESOURCE_ID,CAPACITY                                          × R
K
ID,WORK_OFFSET,ACTION,RESOURCE_ID,UNITS                       × K
```

**Reader rows:**
- N ≥ 1 and Q ≥ 1, as strict integers (`2.5` and `1_0` are rejected).
- IDs are unique, non-empty and contain no whitespace.
- ARRIVAL ≥ 0; PRIORITY ≥ 1; SERVICE ≥ 1; CATEGORY is non-empty.
- SPACE_REQ is 1–6; TABLE_REQ is 0 (the Library has no TABLE pool).

**Resources:**
- Only names from the inventory in §2, each declared once, with CAPACITY 1.

**Actions:**
- `ACQUIRE` or `RELEASE`, with UNITS 1, a known reader and a declared resource.
- `WORK_OFFSET` is 0..SERVICE. It counts the reader's own executed service
  units, not clock time.
- Offsets must not decrease within a reader. Rows at the same offset run in
  file order.
- A RELEASE must name a book the reader holds at that point.
- Every ACQUIRE needs a later RELEASE; a RELEASE at offset SERVICE is allowed.

Trailing blank lines, CRLF line endings and a UTF-8 byte-order mark are
accepted. If R is given, both sections and their exact row counts must be
present. An unchanged A2 input is a valid Final input with R = K = 0.

Bad input never hangs or produces a traceback. It prints
`Error: line N: <reason>` on stderr, exits with status 1, and writes no
output file.

### Command line

```text
python3 main.py INPUT_FILE SCHEDULER ALLOCATOR OUTPUT_FILE [--policy ROLLBACK|ORDERED] [--trace FILE|-] [--stats] [--quiet]
python3 main.py --demo-deadlock [INPUT_FILE] [--policy NONE|ROLLBACK|ORDERED]
```

| Argument | Values |
|---|---|
| `SCHEDULER` | `FCFS`, `PRIORITY` (case-sensitive) |
| `ALLOCATOR` | `FIRST_FIT`, `BEST_FIT`, `WORST_FIT` |
| `--policy` | Deadlock prevention. **Default: `ROLLBACK`**, so prevention is always on in normal runs. `ORDERED` is the alternative |
| `--trace FILE` | Write the readable resource-event trace to FILE (`-` means stderr) |
| `--stats` | Print policy counters (rollbacks, reacquisitions, holds while waiting, …) and wall-clock times to stderr |
| `--demo-deadlock` | The bounded unsafe demonstration (§10). It uses `inputs/deadlock_unsafe.txt` unless another input is given |

**Exit status:**
- **0**: success.
- **1**: handled input, usage or I/O error. A message is printed and no output file is written.
- **2**: the run finished but some readers did not complete. The report is
  still written, with the CHECK lines showing why.

Trace, statistics and errors never go into the output file.

### Output (spec §9.2)

The output is one UTF-8, comma-separated file with `\n` line endings, no
header row and no extra text:

```text
PROCESS,ID,ARRIVAL,PRIORITY,SERVICE,START,COMPLETION,WAITING,TURNAROUND,RESPONSE,MEM_ADMIT,MEM_WAIT,READY_WAIT,RESOURCE_WAIT
SUMMARY,AVERAGE_WAITING,value
SUMMARY,AVERAGE_TURNAROUND,value
SUMMARY,AVERAGE_RESPONSE,value
SUMMARY,THROUGHPUT,value
SUMMARY,SERVICE_UTILIZATION_PCT,value
SUMMARY,AVERAGE_MEMORY_WAIT,value
SUMMARY,COMPLETED_COUNT,value
SUMMARY,BLOCKED_FOR_MEMORY_COUNT,value
POOL,SPACE,6,PEAK_OCCUPIED,UTILIZATION_PCT,MAX_EXT_FRAG_SLOTS
RESOURCE,RESOURCE_ID,CAPACITY,MAX_SIMULTANEOUS_HOLDERS,ACQUISITIONS,WAIT_EVENTS
CHECK,EXCLUSIVITY_VIOLATIONS,value
CHECK,UNRESOLVED_DEADLOCKS,value
CHECK,COMPLETED_COUNT,value
```

**Ordering:**
- PROCESS lines are sorted by ID as strings, so `R10` comes before `R2`.
- RESOURCE lines are sorted by resource ID, one per declared resource.

**Values:**
- Times and counts are integers. Every decimal uses exactly 4 places
  (`3.6667`), and percentages are percent values (`75.0000`).
- The three CHECK values are measured, not hard-coded.
  - `EXCLUSIVITY_VIOLATIONS` is the larger of the manager's own count and
    the count from an independent replay of the trace.
  - `UNRESOLVED_DEADLOCKS` is the number of wait-for cycles left at the end.
- Resource-free input gives the A2 lines with `RESOURCE_WAIT` = 0 appended,
  no RESOURCE lines, and `CHECK` 0 / 0 / N.

Output of the spec's sample workload (`inputs/spec_sample.txt`, FCFS,
FIRST_FIT, ROLLBACK):

```text
PROCESS,R1,0,1,6,0,11,5,11,0,0,0,0,5
PROCESS,R2,0,3,6,0,6,0,6,0,0,0,0,0
SUMMARY,AVERAGE_WAITING,2.5000
SUMMARY,AVERAGE_TURNAROUND,8.5000
SUMMARY,AVERAGE_RESPONSE,0.0000
SUMMARY,THROUGHPUT,0.1818
SUMMARY,SERVICE_UTILIZATION_PCT,54.5455
SUMMARY,AVERAGE_MEMORY_WAIT,0.0000
SUMMARY,COMPLETED_COUNT,2
SUMMARY,BLOCKED_FOR_MEMORY_COUNT,0
POOL,SPACE,6,2,25.7576,0
RESOURCE,JOURNAL,1,1,2,0
RESOURCE,REFERENCE_BOOK,1,1,2,1
CHECK,EXCLUSIVITY_VIOLATIONS,0
CHECK,UNRESOLVED_DEADLOCKS,0
CHECK,COMPLETED_COUNT,2
```

Both readers request `REFERENCE_BOOK` at t = 0 on different worker threads,
which is a genuine race. In the output above R2 won, so R1 waited 5 units
(`RESOURCE_WAIT` = 5).
- If R1 wins instead, the two readers swap roles and the last POOL field
  becomes 1.
- Both outcomes are valid. The spec does not fix the order of racing thread
  events (§9.2); it grades the invariants, which hold either way.

---

## 5. Retained A1 and A2 algorithms

### Scheduling (A1, unchanged)

| Scheduler | Next reader | Key |
|---|---|---|
| `FCFS` | Earliest arrival, then smaller ID | `(arrival, id)` |
| `PRIORITY` | Smaller priority number, then earlier arrival, then smaller ID | `(priority, arrival, id)` |

- Both schedulers are non-preemptive: a reader being served is never
  interrupted.
- IDs compare as strings. Q is read and validated but not used.
- The Library requires only FCFS and PRIORITY (spec §7). Round Robin,
  preemptive priority and quantum expiry do not apply.
- A reader returning from BLOCKED_RESOURCE keeps its original arrival time
  in the key.
- The Python A1 port reproduces the original C++ A1 output byte for byte:
  20/20 golden cases and 6,000 random cross-checks.

### Memory allocation (A2, unchanged)

The six seats are a contiguous pool. A *free run* is a maximal block of
adjacent empty seats.

| Allocator | Chooses |
|---|---|
| `FIRST_FIT` | The first run, scanning from seat 0, that is long enough |
| `BEST_FIT` | The smallest run that is long enough |
| `WORST_FIT` | The largest run that is long enough |

- When two runs tie on size, the one at the lower index wins.
- A reader is always placed at the lowest index of the chosen run.
- On completion exactly that reader's seats are freed, and neighbouring
  free runs merge into one. There is no compaction.

**FIFO admission.** Readers queue for seats in arrival order, with ties
broken by ID.
- Only the head of the queue is tried.
- If the head does not fit, no later reader may skip ahead of it, even one
  that would fit (head-of-line blocking).
- After each successful admission, the new head is tried straight away.

---

## 6. Metrics

For reader *i*: A = arrival, M = memory admission, S = first dispatch,
C = completion, B = service.

| Field | Definition |
|---|---|
| `TURNAROUND` | C − A |
| `RESPONSE` | S − A. S is the first dispatch, even if the reader blocks on a book at offset 0 |
| `WAITING` | C − A − B |
| `MEM_WAIT` | M − A |
| `RESOURCE_WAIT` | Total virtual time spent in BLOCKED_RESOURCE |
| `READY_WAIT` | WAITING − MEM_WAIT − RESOURCE_WAIT |

So **C − A − B = MEM_WAIT + READY_WAIT + RESOURCE_WAIT** for every reader,
as the spec requires (§7). Time spent blocked on a book is never counted as
ready-queue time. `metrics.py` checks this identity and A ≤ M ≤ S ≤ C on
every run.

With E = max C − min A:

| Summary | Definition |
|---|---|
| `THROUGHPUT` | N / E |
| `SERVICE_UTILIZATION_PCT` | ΣB / (2E) × 100. Blocked readers do not hold a librarian, so ΣB is exactly the librarians' busy time |
| `AVERAGE_MEMORY_WAIT` | Mean of MEM_WAIT |
| `BLOCKED_FOR_MEMORY_COUNT` | Readers with M > A |
| Pool `UTILIZATION_PCT` | Occupied seat-time / (6 × E) × 100, time-weighted |
| `PEAK_OCCUPIED` | The highest number of occupied seats seen |
| `MAX_EXT_FRAG_SLOTS` | The highest value seen of (free seats − largest free run) |
| `MAX_SIMULTANEOUS_HOLDERS` | The most holders a resource had at once (never above 1) |
| `ACQUISITIONS` | Successful grants of the resource, including re-grants after a rollback |
| `WAIT_EVENTS` | ACQUIRE requests for the resource that were refused and blocked |

---

## 7. Virtual time and real threads

There are two separate notions of time (spec §13).

| | Virtual simulation time | Real thread execution |
|---|---|---|
| What it is | An integer clock owned by the coordinator | Real OS threads (`worker-1`, `worker-2`) scheduled by the operating system |
| What uses it | Arrivals, service progress, completions, every reported metric | Running ACQUIRE/RELEASE against the shared `ResourceManager` |
| How it advances | Jumps to the next event; no `sleep()` | Threads run as the OS schedules them; batches use a barrier only to make overlap observable |
| Deterministic? | Yes, given the same order of resource grants | No. When two readers race for the same book, either may win |

- A service unit has no fixed wall-clock length. A run that covers 37
  virtual units takes a few milliseconds.
- Worker threads report each result as done or blocked, plus the readers
  they woke. The coordinator turns those results into virtual-time
  timestamps.
- So the metrics are always internally consistent, even when the thread
  interleaving differs between runs.
- Without resource actions no worker thread runs at all, and the output is
  deterministic and identical to A2.
- In CPython the GIL lets only one thread run Python bytecode at a time.
  Threads are still switched between steps, so an unprotected check followed
  by an update can still race. Every ownership check and its update
  therefore happen inside a single lock.
- Free-threaded Python and PyPy have not been tested.

---

## 8. Worker threads and synchronization

- **Thread model.** The coordinator runs the virtual clock, the A1
  scheduler, A2 admission and the reader lifecycle on the main thread
  (spec §4.1 explicitly allows this). The book operations run on a
  `WorkerPool` built on `concurrent.futures.ThreadPoolExecutor`, with 2
  threads named `worker-N`. Each worker gets an *action batch*: one reader's
  due actions at its current offset. It runs them in order until they finish
  or the first ACQUIRE is refused. Workers never touch `Reader` objects,
  queues or seats.
- **Showing real overlap.** When two or more batches are due together, the
  pool sends them in waves of at most 2. The threads in a wave meet at a
  `threading.Barrier` (5-second timeout) before touching any resource, so
  they really run at the same time.
  - The pool measures each batch's real start and end time.
  - Overlapping intervals appear in the trace as `[overlap] worker-1 [...]
    and worker-2 [...] in real execution`.
  - A single batch skips the barrier.

| Shared state | Protected by |
|---|---|
| Resource ownership, waiter queues, counters, wait-for graph | One `threading.Lock` in `ResourceManager`. Every check and its update happen in one critical section; there is no unprotected check-then-act |
| Trace event list and output stream | `threading.Lock` in `Tracer` |
| Batch ordering | Results are collected from futures in submission order. The coordinator applies them only after every batch at *t* has finished |
| Reader states, READY queue, admission queue, seats | Owned by the coordinator thread alone, so they need no lock |

- **No sleeps or busy-waiting.** Nothing uses `sleep()` or polling for
  correctness. A refused ACQUIRE returns BLOCKED immediately; the worker
  does not wait on it.
- **How a blocked reader is resumed.** The reader is recorded as a waiter.
  The release that frees the book hands it over under the same lock and
  reports the woken reader. The coordinator then makes that reader READY
  (spec §5.2, "rescheduled through an equivalent thread-safe event
  mechanism").
- **Thread-level demo.** `deadlock.run_blocking_demo()` shows the same
  deadlock with two threads on a `threading.Condition` with timed waits. It
  is optional and callable from Python.

---

## 9. Resource ownership, blocking and wake-up

- **ACQUIRE of a free book** grants it immediately. Under the lock it
  records the holder, adds 1 to `ACQUISITIONS`, and updates the
  simultaneous-holder count.
- **ACQUIRE of a held book** is refused.
  - The reader is queued as a waiter and becomes BLOCKED_RESOURCE.
  - It gives up its librarian but keeps its seats.
  - Its `WAIT_EVENTS` count rises by 1, and it uses no service time while
    blocked.
  - The prevention policy decides what happens to books it already holds (§10).
- **RELEASE** must come from the current holder; anything else is an
  invalid release. The book goes straight to the first eligible waiter
  while the lock is still held. So the woken reader already owns it when it
  is dispatched again, and no third reader can grab it first.
  - This rules out lost wake-ups.
  - It also rules out stranded waiters whose book is free.
- **Resuming.** The woken reader becomes READY with its original scheduling
  key and must win a librarian again. The ACQUIRE that blocked it is not run
  again. `RESOURCE_WAIT` grows by exactly the virtual time it spent blocked.
- **Completion** requires all service done and every action run, so a
  reader can never finish while holding a book. The engine's end-of-run
  check fails the run if any book is still held, seats are still occupied,
  or a queue is not empty.

Fairness assumptions (the spec does not require strict fairness, §5.2):

- **NONE:** each book has a FIFO queue of waiters.
- **ROLLBACK:** one global queue, scanned for the first waiter whose *whole*
  set of books is free. A waiter that cannot yet be satisfied can be
  overtaken by a later one.
- **ORDERED:** each book has its own FIFO queue. A reader may pass through
  several queues while re-acquiring books.

None of the policies guarantees freedom from starvation, and no fairness
of the OS lock is assumed.

---

## 10. Deadlock: conditions, demonstration and prevention

### The four conditions in the Library (spec §6.1)

| Condition | Present in the Library? |
|---|---|
| **Mutual exclusion** | Yes. Each named copy has at most one holder |
| **Hold and wait** | Yes. A reader can keep `REFERENCE_BOOK` while waiting for `JOURNAL` |
| **No preemption** | Yes. A book is returned only by the holder's own RELEASE. Scheduling is non-preemptive too, but that is a different matter |
| **Circular wait** | Possible. R1 holds `REFERENCE_BOOK` and wants `JOURNAL`, while R2 holds `JOURNAL` and wants `REFERENCE_BOOK` |

All four together are needed for a deadlock. Each prevention policy breaks
one of them.

### Bounded unsafe demonstration (spec §6.2, §6.4)

`inputs/deadlock_unsafe.txt` is the spec's sample with R2's acquisition
order reversed. `python3 main.py --demo-deadlock` runs the real engine on it
once per policy:

```text
NONE: deadlocked=True completed=
ROLLBACK: deadlocked=False completed=R1,R2
ORDERED: deadlocked=False completed=R1,R2
```

Under `NONE` (no prevention, demo only), both readers take their first book
at t = 0 on two worker threads. At t = 1 each requests the other's book and
blocks:

```text
[t=0 #9 worker-2]   R2 ACQUIRE JOURNAL
[t=0 #10 worker-1]  R1 ACQUIRE REFERENCE_BOOK
[t=1 #11 worker-1]  R2 BLOCK REFERENCE_BOOK (held by R1)
[t=1 #12 worker-2]  R1 BLOCK JOURNAL (held by R2)
[t=1 #13 MainThread] R1 DEADLOCK (R1->R2->R1)
```

**Why it stops instead of hanging:**
- Once nobody is running and no future arrival or action is left, the
  virtual clock has nowhere to go. The engine then checks the wait-for graph
  (`find_cycles`), reports the cycle and stops.
- No thread is ever parked waiting for a lock, so nothing can hang, and no
  watchdog timer is needed.
- Run through the normal command line with `--policy NONE`, the same input
  writes `CHECK,UNRESOLVED_DEADLOCKS,1`, prints
  `Error: run finished with unfinished readers: R1, R2 (deadlock cycles: 1)`
  and exits 2.

### Prevention policies (spec §6.3)

Prevention is always on in normal runs; the default is **ROLLBACK**.

**ROLLBACK breaks hold and wait (all or nothing).**
- If a requested book is free, it is granted.
- If it is busy and the reader holds nothing, the reader simply waits.
- If it is busy and the reader holds a set H, the reader releases all of H
  (a rollback) and waits for H plus the requested book. The whole set is
  granted at once, as soon as every book in it is free.
- So a waiting reader never holds a book (`held_while_waiting` = 0 in every
  measured run), and no wait-for cycle can form.
- Work offsets are not rewound. The reader continues from where it stopped,
  with all its books back.

**ORDERED breaks circular wait (global order).**
- Books are ranked in lexicographic order of their declared IDs, so
  `JOURNAL` comes before `REFERENCE_BOOK` and `OS_BOOK_10` before `OS_BOOK_2`.
- A free book is granted in any order.
- When a reader must wait for book X:
  - it keeps the books it holds that rank below X;
  - it releases those that rank above X;
  - it then gets X and the released books back in ascending rank order.
- Every waiting reader is therefore waiting for a book ranked above all the
  books it holds, so the waits can never form a cycle.
- In the demo:
  - R1 holds `REFERENCE_BOOK` and needs `JOURNAL`, which ranks lower. It
    releases `REFERENCE_BOOK`, and R2 receives it.
  - R2 finishes at t = 6.
  - R1 gets `JOURNAL` at t = 5 and `REFERENCE_BOOK` back, then completes at
    t = 10.

**Why release-and-reacquire instead of rejecting:** inputs list actions in
any order, and the spec expects every valid input to complete. So neither
policy rejects an out-of-order request; both repair it at run time.

**Limitations.**
- ROLLBACK adds extra book handovers and re-grants, and a reader that wants
  a large set of books can be overtaken repeatedly.
- ORDERED lets readers hold books while waiting (convoys) and may also roll
  books back.
- Neither prevents starvation.

§13 shows the effect on throughput, fairness and utilization.

---

## 11. Resource-event trace

`--trace FILE` (or `-` for stderr) writes a readable log, kept separate from
the graded output (spec §5.3). Each line has the form
`[t=<virtual time> #<sequence> <thread name>] <reader> <event> [details]`.

| Events | Recorded by |
|---|---|
| `ACQUIRE`, `BLOCK (held by …)`, `RELEASE`, `HANDOFF (from …)`, `ROLLBACK` | The worker thread that performed the operation, inside the resource lock |
| `ARRIVE`, `BLOCK_MEMORY` (joined the seat queue), `ADMIT (seats=a-b)`, `DISPATCH (librarian=n)`, `UNBLOCK`, `COMPLETE`, `DEADLOCK` | `MainThread` (the coordinator) |
| `[overlap] worker-1 [...] and worker-2 [...]` | Real start and end times of two batches that ran at the same moment |

A full trace of the spec sample is in
[docs/aarush/overlap_evidence.txt](../docs/aarush/overlap_evidence.txt).
Mutual exclusion can be read straight from the trace: between a book's
ACQUIRE or HANDOFF and its RELEASE or ROLLBACK, no other reader holds it.
`trace.audit_exclusivity` replays the trace mechanically, and its count feeds
`CHECK,EXCLUSIVITY_VIOLATIONS`.

---

## 12. Final challenge evidence

Each item below can be reproduced from the archive (spec §10 and §13).

**1. Scheduling: FCFS and PRIORITY change order and waiting.**
```bash
python3 main.py inputs/a2/comparison.txt FCFS FIRST_FIT fcfs.txt
python3 main.py inputs/a2/comparison.txt PRIORITY FIRST_FIT prio.txt
```
| | Average waiting | Average memory wait | Throughput | Service utilization | Last completion |
|---|---|---|---|---|---|
| FCFS | 5.5000 | 0.9000 | 0.3030 | 95.4545 | 35 |
| PRIORITY | 5.9000 | 1.2000 | 0.2857 | 90.0000 | 37 |

**2. Memory: the allocators change placement and fragmentation.**

With the same input, the six combinations give these values for maximum
external fragmentation:

| | FIRST_FIT | BEST_FIT | WORST_FIT |
|---|---|---|---|
| FCFS | 2 | 0 | 1 |
| PRIORITY | 2 | 1 | 1 |

- At t = 5, R04 needs 2 seats and the free runs are 0–2 and 4–5. Best Fit
  takes 4–5, while First Fit and Worst Fit take 0–1.
- Under PRIORITY, Worst Fit also admits R02 one unit earlier (memory wait
  1.1000 against 1.2000).
- `inputs/a2/` has eight more edge cases: head-of-line blocking, fragmented
  waits, equal holes and coalescing, request sizes 1 and 6, simultaneous
  arrivals, initial idle time, long gaps, and a completion and an arrival at
  the same moment. Each has the expected output for all six combinations in
  `tests/expected/a2/`.

**3. Concurrency: two real workers; a book is never held twice; different copies are held at the same time.**
```bash
python3 main.py inputs/spec_sample.txt FCFS FIRST_FIT out.txt --trace -
python3 main.py inputs/different_copies.txt FCFS FIRST_FIT out.txt --trace -
```
- **Spec sample:** `worker-1` and `worker-2` race for `REFERENCE_BOOK`, and
  an `[overlap]` line shows both batches running at the same moment. One
  reader gets the book. The other is refused (`BLOCK … (held by …)`) and
  later receives it as a `HANDOFF`.
- **`different_copies.txt`:** R1 holds `OS_BOOK_3` while R2 holds
  `OS_BOOK_7`, both from t = 0 on different threads. Later R3 takes
  `OS_BOOK_3`.
- Every run reports `CHECK,EXCLUSIVITY_VIOLATIONS,0`, and no RESOURCE line
  reports more than 1 holder.

**4. Deadlock:** `python3 main.py --demo-deadlock` (see §10).

**5. Integration: a blocked reader gets no service, and a release lets others continue.**
```bash
python3 main.py inputs/memory_blocking_interaction.txt FCFS FIRST_FIT out.txt --trace -
python3 main.py inputs/reader_blocked_holding.txt FCFS FIRST_FIT out.txt --trace -
```
- **`memory_blocking_interaction.txt`** (all times FCFS):
  - R1 takes seats 0–3. R2, which needs 3 seats, is stuck at the head of
    the queue.
  - R3 needs only 1 seat but cannot overtake R2.
  - R1's completion at t = 4 lets both in, and only then are they
    dispatched: `MEM_WAIT` 4 and 3, `START` 4.
  - The `JOURNAL` R1 releases at t = 3 is the one R2 acquires at t = 4.
- **`reader_blocked_holding.txt`:**
  - R1 holds `REFERENCE_BOOK` and blocks on `JOURNAL`, which R2 holds.
  - R1 gives up its librarian and its book is rolled back.
  - R2's release at t = 3 hands both books to R1, which is dispatched again
    (`RESOURCE_WAIT` = 1).

---

## 13. Observed comparison results

### Allocators (A2 baseline, `inputs/a2/comparison.txt`)

| Scheduler | Allocator | Avg wait | Avg memory wait | Seat utilization % | Max fragmentation | Last completion |
|---|---|---:|---:|---:|---:|---:|
| FCFS | FIRST_FIT | 5.5000 | 0.9000 | 69.1919 | 2 | 35 |
| FCFS | BEST_FIT | 5.5000 | 0.9000 | 69.1919 | 0 | 35 |
| FCFS | WORST_FIT | 5.5000 | 0.9000 | 69.1919 | 1 | 35 |
| PRIORITY | FIRST_FIT | 5.9000 | 1.2000 | 63.3333 | 2 | 37 |
| PRIORITY | BEST_FIT | 5.9000 | 1.2000 | 63.3333 | 1 | 37 |
| PRIORITY | WORST_FIT | 5.9000 | 1.1000 | 64.2857 | 1 | 37 |

Every row is checked by hand and against an independent reference
implementation. See [allocator results](../docs/aarush/allocator_comparison.md),
[manual checks](../docs/aarush/fixture_checks.md) and
[the full workbook](../docs/aarush/fixture_derivations.md).

### Prevention policies (720 measured runs)

The setup was 6 workloads (`inputs/policy/p1`–`p6`) × 2 schedulers ×
2 policies × 30 repeats, all with FIRST_FIT. **All 720 runs completed, with
0 violations and 0 deadlocks.** The table shows means:

| Workload | Scheduler | Avg wait R / O | Worst resource wait R / O | Rollbacks R / O | Held while waiting R / O |
|---|---|---|---|---|---|
| P1 in order, low contention | both | 2.50 / 2.50 | 5 / 5 | 0 / 0 | 0 / 0 |
| P2 in order, high contention | both | 7.67 / 7.67 | 13 / 13 | 2 / 1 | 0 / 1 |
| P3 reversed, circular | both | 3.67 / 4.00 | 7 / 7 | 1 / 1 | 0 / 1 |
| P4 out of order, uncontended | both | 0.00 / 0.00 | 0 / 0 | 0 / 0 | 0 / 0 |
| P5 multi-book vs single | FCFS | 2.75 / 2.75 | 5 / 5 | 0 / 0 | 0 / 0 |
| P5 multi-book vs single | PRIORITY | 1.50 / 1.50 | 3 / 3 | 0 / 0 | 0 / 0 |
| P6 12-reader stress | FCFS | 19.75 / 24.92 | 26 / 49 | 10 / 7 | 0 / 7 |
| P6 12-reader stress | PRIORITY | 20.17 / 25.67 | 23 / 40 | 7 / 8 | 0 / 7 |

R = ROLLBACK, O = ORDERED. More metrics (min/max spreads, throughput,
utilization, wall time) are in the
[policy report](../docs/aarush/policy_comparison.md) and its
[JSON data](../docs/aarush/policy_results.json).

**What the measurements show:**
- With low contention or consistent orders (P1, P4, P5), the two policies
  behave identically.
- Under heavy contention (P6), ROLLBACK has about 20 % lower average
  waiting and roughly half the worst-case resource wait. It also has higher
  throughput (0.226 against 0.207 under FCFS) and higher librarian
  utilization (90.6 % against 82.8 %).
- ORDERED needs fewer rollbacks in P2 and in P6 under FCFS, so it hands
  books back and forth less. But its readers hold books while waiting
  (7 holds in P6), which blocks others.
- **Choice of default:** ROLLBACK, because it was never worse on waiting or
  throughput in these workloads, and it keeps held-while-waiting at 0.
  This is not a universal optimum.

---

## 14. Trade-offs

These are the trade-offs between waiting time, throughput, utilization,
fairness, synchronization overhead and deadlock avoidance (spec §10). No
single configuration is best on every measure.

- **FCFS vs PRIORITY (waiting time vs fairness).** PRIORITY serves
  low-numbered readers first. On the comparison workload it raised average
  waiting from 5.50 to 5.90 and lowered throughput from 0.303 to 0.286.
  Its benefit is response time for urgent readers, not efficiency. Without
  aging, a steady stream of high-priority readers could starve low-priority
  ones. FCFS is fair in arrival order but ignores urgency.
- **Allocators (fragmentation vs simplicity).** Best Fit kept the most
  contiguous space (fragmentation 0 under FCFS) by filling small gaps.
  First Fit is the simplest and the fastest to find a place, but left 2
  scattered seats. Worst Fit keeps large remainders, but uses up the biggest
  free run. With six seats and FIFO admission, the choice mostly changed
  fragmentation, not waiting. Only Worst Fit under PRIORITY moved 0.1 units
  of waiting from the seat queue to the ready queue.
- **FIFO admission (fairness vs utilization).** A strict queue cannot be
  overtaken, so nobody starves for seats. The cost is head-of-line blocking:
  in `memory_blocking_interaction.txt`, R3 needs one free seat but waits
  3 units behind R2, while a librarian sits idle.
- **Keeping seats while blocked on a book (simplicity vs utilization).**
  Seats stay reserved for a reader blocked on a book. That keeps admission
  simple and avoids repeated re-admission, but those seats are idle while
  the reader waits.
- **ROLLBACK vs ORDERED (deadlock avoidance vs overhead).**
  - Both rule deadlock out. ROLLBACK does it by never letting a waiting
    reader hold anything. That lowered waiting and raised throughput and
    utilization under contention (P6), at the cost of more re-grants
    (`ACQUISITIONS` 42 against 38 in P6 under FCFS).
  - ORDERED moves books around less, but allows convoys: a reader holding a
    low-ranked book while it waits blocks others.
  - Neither guarantees fairness; ROLLBACK can keep overtaking a reader that
    wants many books.
- **Synchronization overhead.** One global resource lock makes every check
  and its update atomic and easy to reason about. With 17 books and 2
  workers it is never the bottleneck; a full run of a bundled workload takes a few milliseconds. The
  barrier that forces overlap adds some wall-clock time but changes no
  virtual-time result. Finer-grained locks per book would add complexity
  and the risk of lock-order deadlocks, for no measurable gain here.
- **Real concurrency vs determinism.** Real threads mean racing requests
  can be settled differently between runs. The engine therefore keeps every
  metric derived from one consistent virtual timeline, and checks the
  invariants (exclusivity, no deadlock, conservation) rather than an exact
  order of events.

---

## 15. Testing

```bash
python3 -m unittest discover -s tests -t . -v      # 173 tests in the source repo
python3 -m unittest tests.contract.test_pyi_conformance -v
```

**`tests/contract/`: one test file per module.** These cover:
- the parser's validation rules, each with its error line;
- placement for each allocator and FIFO admission;
- scheduler tie-breaking;
- metric identities and the output format;
- resource policies, handoff and invalid releases;
- worker overlap (distinct threads, overlapping time intervals);
- trace replay, cycle detection and the demo;
- randomized stress tests of exclusivity and conservation.

`test_pyi_conformance` checks every module against the interface contract
in `library_sim.pyi`.

**`tests/integration/`: cross-module tests.**
- The engine matches the Python A1 port on 211 inputs when memory never
  blocks.
- All 54 expected A2 outputs are reproduced exactly, and repeated runs are
  identical.
- Resource-free Final runs equal A2 for every scheduler and allocator.
- Bad command-line arguments exit 1 and write no file.
- The end-of-run invariant check fires when state is left behind.

**What the source repository's checks covered** (Python 3.10 and 3.14):
- All 173 root tests pass (one test skips by design).
- The standalone A1 suite has 17 tests and 20/20 golden cases.
- 3,600 random contended Final runs under both policies finished with no
  crash, hang, deadlock or exclusivity violation.

---

## 16. Assumptions

**Confirmed with the TA:**
1. START is the first dispatch to a librarian, even if the reader then
   blocks on an ACQUIRE at offset 0, so RESPONSE = S − A.
2. Order within one timestamp: resource actions (including RELEASE at
   offset SERVICE) → completions → arrivals → memory admission → wake-ups
   from releases → dispatch → actions due immediately after dispatch. This
   repeats until nothing changes. Released books go directly to the first
   eligible waiter.
3. A reader returning from BLOCKED_RESOURCE keeps its original arrival time
   in the scheduler key. Scheduling remains non-preemptive.
4. Peak occupancy and fragmentation are sampled once, at the end of each
   timestamp. States that exist only in the middle of a timestamp are
   ignored.
5. Resource-free Final input still gets the CHECK lines (0, 0, N) but no
   RESOURCE lines. The A2 program never writes CHECK lines.
6. Every decimal statistic has 4 decimal places, and percentages are
   percent values.

**Our own choices:**
- E = max C − min A, so the observation window starts at the first arrival,
  as in A1.
- Offsets are not rewound after a rollback.
- `RESOURCE` lines are written for every declared resource, even when K = 0.
- A woken reader already owns every book it needs before it becomes READY.
- Book ranks for ORDERED use lexicographic ID order.
- A free book is granted whatever its rank. Only a wait has to follow
  ascending rank.
- Seat pool capacity can be changed only for tests. Inputs are still
  limited to SPACE_REQ 1–6.
- The exit codes are 0, 1 and 2, as described in §4.

**Not applicable to the Library:**
- Only non-preemptive FCFS and PRIORITY are required (spec §7). Round Robin,
  preemptive priority and quantum expiry therefore do not exist, and Q is
  validated but unused.
- The TABLE pool belongs to the Restaurant scenario, so TABLE_REQ must be 0.
- Blocking on a book means giving up the librarian voluntarily, which is
  consistent with non-preemptive scheduling. A policy rollback of books is
  not preemption of service.

---

## 17. Limitations

- PRIORITY has no aging, so low-priority readers could starve under a
  continuing high-priority stream.
- FIFO admission can leave seats idle behind a head reader that does not
  fit. There is no compaction.
- Racing requests may be settled differently between runs. Fixed inputs do
  not make contended Final runs byte-for-byte repeatable; the spec allows
  this. Resource-free runs are fully deterministic.
- Neither prevention policy guarantees starvation freedom or global
  fairness.
- The normal command line also accepts `--policy NONE`, which is meant only
  for the demo. Such a run is bounded, reports the deadlock in the CHECK
  lines and exits 2.
- **Trace wording:**
  - When ROLLBACK grants several books at once, every `HANDOFF` names the
    reader whose release completed the set, even for a book someone else
    released earlier.
  - `UNBLOCK` is logged during the action step, before that timestamp's
    completions and arrivals. No difference in scheduling results from
    the approved order has been found.
  - `BLOCK_MEMORY` is logged on every arrival (the reader joining the seat
    queue), even if it is admitted at the same timestamp.
- `out_of_order_requests` in `--stats` is counted only under ORDERED, so it
  cannot be compared across policies.
- `run_blocking_demo()` reports placeholder pool statistics.
- Free-threaded Python and PyPy have not been tested.
- Writing the output file is not atomic: a failure while writing can leave
  a partial file.

For the full list with reproductions, see the
[implementation audit](../docs/implementation_audit.md).

---

## 18. Optional features

**Built:**
- `--trace`, with thread names and real-overlap evidence.
- `--stats`: policy counters and wall-clock times.
- Two prevention policies that can be selected per run.
- Wait-for cycle detection, used in the demo.
- A thread-level blocking demo built on a `Condition`.
- The `experiments` comparison tool, with Markdown and JSON reports.
- A reproducible random stress workload (`inputs/policy/generate_stress.py`, seed 3710).
- Randomized stress tests.
- An independent A2 reference implementation used to check the expected outputs.
- Interface conformance tests.

**Not built:** a runtime memory map or timeline view, wait-for graph
visualization, and resource queues that are fair or prevent starvation.

---

## 19. Requirements checklist

Final spec §15:

| Requirement | Where |
|---|---|
| A1 schedulers kept (FCFS, PRIORITY; two librarians) | §5, `scheduler.py`, A1 regression tests |
| A2 allocators and FIFO admission kept | §5, `memory.py`, 54 expected outputs |
| Real concurrent workers, correct synchronization | §8, `workers.py`, `resources.py`, overlap tests |
| Contention for shared resources | §9, §12 item 3, `inputs/policy/` |
| Bounded deadlock demo, prevention on by default | §10, `--demo-deadlock`, default `ROLLBACK` |
| Full integration (memory → schedule → resources → completion) | §3, §12 item 5 |
| Standard input and output | §4, contract and golden tests |
| Full README | This file |
| Final archive runs on its own | `build_packages.py` checks the unzipped archive |

---

## 20. Code layout and ownership

```text
main.py                 entry point (Final)
library_sim/            the package (src/library_sim/ in the source repo)
library_sim.pyi         interface contract shared by every module
inputs/                 spec sample, demo inputs, a2/ edge cases, policy/ workloads
tests/                  contract/, integration/, fakes/, expected/a2/
docs/                   section guides, measurements, audit, memory-management PDF
```

| Member | Modules |
|---|---|
| Kabir | Python A1 port, `models`, `errors`, `scheduler`, `parser`, `metrics`, `output`, interface contract |
| Aarush | `memory`, `experiments`, A2 edge cases and expected outputs, A2 README, comparisons |
| Urvashi | `engine`, `cli`, `build_packages.py`, integration |
| Samar | `resource_parser`, `resources`, `workers`, `trace`, `deadlock`, policy workloads |

More detail:
- [concurrency and deadlock guide](../docs/readme/samar_concurrency_deadlock.md)
- [memory and comparison guide](../docs/readme/aarush_memory_comparison.md)
- [algorithms, metrics and output](../docs/readme/kabir_algorithms_metrics_output.md)
- [engine and CLI](../docs/readme/urvashi_engine_cli.md)
- [memory-management PDF guide](../docs/aarush/README.md)
