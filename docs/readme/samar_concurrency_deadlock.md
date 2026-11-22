# Concurrency, synchronization, and deadlock prevention

**Implementation owner:** Samar (`sam-b02`).

**Audited code:** `f69cd13`, 22 November 2026, Python 3.12.3.

**Evidence:** [implementation audit](../implementation_audit.md).

The five Final modules are implemented. Integrated samples pass, but worker
overlap evidence, some contract details, measured comparisons, and complete
submission packaging remain unfinished. S1–S9 are assigned work items; this
document does not mark every subtask complete.

## Library resources and deadlock conditions

Readers obtain seats through A2 admission before a librarian serves them.
During service they can acquire declared named books or journals, each with
capacity one. Different copies, such as OS_BOOK_3 and OS_BOOK_7, have separate
ownership records and can be held simultaneously.

The unsafe NONE policy illustrates four necessary deadlock conditions:

1. **Mutual exclusion:** a named physical resource has one holder.
2. **Hold and wait:** a reader keeps one book while waiting for another.
3. **No resource preemption:** under NONE, an input RELEASE returns a held
   book. Safe policies can instead force release of some holdings.
4. **Circular wait:** R1 holds REFERENCE_BOOK and waits for JOURNAL while
   R2 holds JOURNAL and waits for REFERENCE_BOOK.

CPU scheduling remains non-preemptive FCFS or Priority. Forcing a book
release is distinct from interrupting a reader's service.

## What each module currently does

| Module | Implemented behavior | Important limit |
|---|---|---|
| `resource_parser.py` | Parses R/K sections; checks named capacity-one resources, units, offsets, references, balanced ownership replay. | Sorts actions first, accepting descending offsets; semantic errors can point to the R-count line. |
| `resources.py` | Locks ownership, waiters, grants/releases, counters, and resource-event emission; implements all three policies. | Fairness and trace shapes depend on policy. |
| `workers.py` | Uses real executor threads; stops at a blocked acquire; propagates exceptions; returns results in input order. | Short batches can all use one worker; overlap is not guaranteed. |
| `trace.py` | Locks enabled event recording and sink writes; records sequence, virtual time, IDs, thread name; replays ownership. | Disabled tracers retain no history to audit. |
| `deadlock.py` | Defines ranks/policies/counters; finds cycles; runs the real-engine unsafe demo when memory exists; offers a separate blocking demo. | A supplied tracer is reused across policies; the optional demo uses synthetic simulation statistics. |

## Coordinator, workers, and synchronization

One coordinator owns virtual time, Reader transitions, the ready queue,
seat pool, and admission queue. Workers receive action batches, not mutable
Reader objects. Actions run sequentially within a batch until its first
blocked ACQUIRE.

`ThreadPoolExecutor` provides real threads named `worker-N`. Resource methods
use one `threading.Lock`: ownership checks and updates share the critical
section. Tracer has a separate lock for its event list and sink writes.
WorkerPool measures intervals and can write an `[overlap]` line to the sink
when distinct workers overlap. This diagnostic is outside the graded output.

An unavailable acquire records a waiter and returns BLOCKED. The coordinator
reschedules readers through this event mechanism rather than parking workers
until virtual time advances. The normal loop uses neither sleep nor resource
polling for correctness. Resource ownership locking does not assume the GIL
makes multi-step operations atomic. Free-threaded Python and PyPy were not
validated, so their correctness is not claimed as a tested result.

**Normal-worker overlap evidence is still pending.** In 100 audit trials,
two short batches used the same worker and recorded no overlap. The existing
overlap test checks only name prefixes. A barrier exists in the separate
blocking demo and a stress test, not in normal WorkerPool submission.

## Blocking, wake-up, and fairness

The coordinator first applies every batch's done/blocked results. A blocked
reader becomes BLOCKED_RESOURCE, records its blocking time, releases its
librarian, and keeps its seats. The coordinator then handles the union of
woken IDs: each already owns what it needs to resume, becomes READY, and
accumulates only the virtual blocked interval in `resource_wait`. The blocked
ACQUIRE advances once and is not executed again.

In the current Final loop, wake processing occurs inside the action round,
before completions and arrivals. This precedes the contract's numbered step 5.
Librarian dispatch still follows admission.

Ownership grants and waiter selection occur under the resource lock. The
actual fairness rules are:

- **NONE:** release grants the book directly to its first queued waiter.
- **ROLLBACK:** a global queue is scanned for the first waiter whose entire
  set is free. Earlier ineligible requests can be bypassed. A rolled-back book
  can remain free while its former holder waits for the rest of its set;
  other readers can acquire it.
- **ORDERED:** each current resource wait has a FIFO queue. A reader may
  advance through several queues while reacquiring its ordered sequence and
  wakes only after obtaining the complete sequence. This is not global
  arrival-order fairness or a starvation-freedom guarantee.

No strict fairness property of the OS lock is assumed.

## Implemented prevention policies

### ROLLBACK — remove hold-and-wait

A free requested resource is granted immediately. If it is busy and the
requester holds nothing, the reader waits for that resource. If it holds a
set H, the manager releases all of H, records a rollback, and queues the
reader for H plus the requested resource. The full set is granted atomically
once all members are free. A queued ROLLBACK reader holds no books;
`held_while_waiting` remains zero in the tested runs.

Work offsets do not rewind. Other readers can benefit from released books,
but reacquisition overhead, additional waiting, or starvation are possible
trade-offs. Removing hold-and-wait does not eliminate every convoy.

### ORDERED — ascending waits to prevent circular wait

Rank is lexicographic order of declared IDs: OS_BOOK_10 precedes OS_BOOK_2.
A free resource can be granted out of order. For a busy resource, the reader
keeps lower-ranked holdings and releases holdings ranked above the request.
It then obtains the request and released books in ascending rank, waiting
at each necessary step. The reader resumes only after the complete sequence.

This policy is intended to maintain ascending wait edges. It may hold books
while blocked, causing convoying. Both safe policies accept all acquisition
orders in the tested bundled samples; this is not proof of progress or
fairness for every possible input.

### Default and comparison status

`DEFAULT_POLICY` is ROLLBACK. It is the current engineering default; a measured
P1–P6 selection is not complete and `experiments.py` is absent. The earlier
winner table has been removed because it presented expectations as results.

A focused P1 audit used FIRST_FIT, both schedulers, and 30 runs per policy:

| Scheduler | Policy | Runs | Rollbacks each run | Total resource wait each run | Last completion each run |
|---|---|---|---|---|---|
| FCFS | ROLLBACK | 30 | 0 | 5 | 11 |
| FCFS | ORDERED | 30 | 0 | 5 | 11 |
| PRIORITY | ROLLBACK | 30 | 0 | 5 | 11 |
| PRIORITY | ORDERED | 30 | 0 | 5 | 11 |

Those P1 metrics tie; no wall-time or fairness winner is established. P2–P6
are fixed candidate examples, not measured winners. P5 has three single-book
readers rather than an unbounded stream; P6 is not a random generator and
its last two readers have no resource actions.

## Trace and statistics details

Resource events are emitted inside the resource lock. The coordinator emits
ARRIVE, BLOCK_MEMORY, ADMIT, DISPATCH, UNBLOCK, COMPLETE, and DEADLOCK. Enabled
tracing is separate from graded output. The engine reports the maximum of
the manager's violation count and trace ownership replay.

Replay checks ACQUIRE/HANDOFF/RELEASE/ROLLBACK ownership, including duplicate
grants and releases by non-holders. It does not validate overlap, provenance,
FIFO behavior, or complete compliance. When tracing is disabled, the empty
history provides no independent ownership evidence.

Multi-resource ROLLBACK grants can emit HANDOFF after the book was freed
and label every grant with the latest releasing reader rather than the book's
actual previous holder. ORDERED also emits all rollback events before their
handoff processing. These differ from CONTRACT 3's immediate per-book event shape.

`acquisitions` includes regrants. Resource `wait_events` counts original
acquires returning BLOCKED, not each internal ORDERED reacquisition wait.
`out_of_order_requests` currently increments only under ORDERED: zero under
ROLLBACK does not prove ascending input order. These counters are not blocked
durations or wall time.

## Running the current code

From the repository root, with Python 3.10+ and no third-party packages:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t . -v
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import final_main; raise SystemExit(final_main(sys.argv[1:]))' inputs/spec_sample.txt FCFS FIRST_FIT /tmp/library-final-output.txt --policy ROLLBACK --trace /tmp/library-final-trace.txt --stats
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import final_main; raise SystemExit(final_main(sys.argv[1:]))' --demo-deadlock
```

The normal CLI advertises ROLLBACK/ORDERED but currently also accepts NONE;
use NONE only for the unsafe demonstration. Incomplete Final runs write a
partial report and return 2. Parser/usage errors return 1 before result writing;
writing errors can leave partial files. Worker RuntimeErrors propagate and
are not among the CLI's caught exceptions.

`run_unsafe_demo()` uses separate tracers by default. Supplying a single Tracer
across policies contaminates later audits with unsafe holdings; this reproduced
two false violations in each safe report. The default sample path is relative
to the working directory, so run from the repository root. Generated ZIPs do
not contain the input: the packaged default demo fails without an external copy.

The optional `run_blocking_demo()` is callable from Python. It uses two actual
threads, a barrier, the same ResourceManager under NONE, and timed condition
waits. It has placeholder pool/timestamp statistics and records the configured
timeout as `wall_time_s`, not measured runtime. It is not a service/policy
benchmark. Its barrier and thread joins have no timeout protection.

## Evidence and remaining work

Root discovery at the audited revision found 134 tests: 133 passed and one
missing-module check was skipped because that module exists. Another 360
integrated sample runs completed with zero reported violations/deadlocks.
Some stress tests do not assert completion or end-of-run conservation; the
different-copy test uses sequential calls. They do not prove every concurrency
claim or complete S7.

Resource/worker fakes exist. The resource fake uses NONE-style ownership
regardless of supplied policy, and the worker fake runs synchronously. Use
real modules for prevention-policy and concurrency validation.

Pending: controlled overlap evidence; the parser, trace, CLI, and shared-tracer
corrections above; stronger regressions; measured policy/default comparisons;
complete READMEs/archive contents; and presentation material. Detailed evidence
and remaining Aarush tasks are in the linked audit.
