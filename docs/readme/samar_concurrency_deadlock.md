# Concurrency, synchronization, and deadlock prevention

**Implementation owner:** Samar (`sam-b02`).

**Current validation:** base `8f256e6` plus the A6/A7 and targeted Sam fixes, Python 3.12.3.

**Evidence:** [implementation audit](../implementation_audit.md).

The five Final modules and full experiment harness are integrated. Controlled
worker overlap, per-run trace isolation, and action ordering/error-line fixes
have regressions. The complete 720-run policy comparison is recorded below.
Other explicitly listed Final limitations and presentation work remain open.

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
| `resource_parser.py` | Parses R/K sections; checks named capacity-one resources, units, offsets, references, balanced ownership replay. | Rejects descending per-reader offsets before replay; semantic action errors carry their source line. |
| `resources.py` | Locks ownership, waiters, grants/releases, counters, and resource-event emission; implements all three policies. | Fairness and trace shapes depend on policy. |
| `workers.py` | Uses real executor threads; stops at a blocked acquire; propagates exceptions; returns results in input order. | Multi-batch waves meet at a bounded barrier before resource operations; one worker/batch needs no barrier. |
| `trace.py` | Locks enabled event recording and sink writes; records sequence, virtual time, IDs, thread name; replays ownership. | Disabled tracers retain no history to audit. |
| `deadlock.py` | Defines ranks/policies/counters; finds cycles; runs the real-engine unsafe demo when memory exists; offers a separate blocking demo. | Each result audits its own event slice even with a shared tracer; the optional demo still has synthetic statistics. |

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

**Controlled overlap is now demonstrated.** WorkerPool submits waves no larger
than worker capacity and meets at a barrier before taking a resource lock.
Start times precede the barrier; end times follow batch operations. The five-second
barrier timeout bounds a broken rendezvous. Results stay in submission order.
Tests assert distinct threads and positive interval overlap, including more
batches than workers, one worker/batch, empty input, contention, and exceptions.
[Actual overlap trace](../aarush/overlap_evidence.txt) records thread names and
real intervals. The engine shuts workers down even if a batch raises.

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

`DEFAULT_POLICY` remains ROLLBACK after validation. Both policies completed
all 720 measured runs safely: six inputs × two schedulers × two policies × 30.
The full [mean/min/max report](../aarush/policy_comparison.md) and
[JSON snapshot](../aarush/policy_results.json) record Python version, seed,
repeats, and instrumentation. FIRST_FIT was used throughout. Wall time includes
in-memory ownership tracing and the same worker barriers for both policies.

The following are observed means, not predicted winners:

| Case | Scheduler | Avg wait ROLLBACK / ORDERED | Worst resource wait R / O | Rollbacks R / O |
|---|---|---|---|---|
| p1 | FCFS | 2.5000 / 2.5000 | 5.0000 / 5.0000 | 0.0000 / 0.0000 |
| p1 | PRIORITY | 2.5000 / 2.5000 | 5.0000 / 5.0000 | 0.0000 / 0.0000 |
| p2 | FCFS | 7.6667 / 7.6667 | 13.0000 / 13.0000 | 2.0000 / 1.0000 |
| p2 | PRIORITY | 7.6667 / 7.6667 | 13.0000 / 13.0000 | 2.0000 / 1.0000 |
| p3 | FCFS | 3.6667 / 4.0000 | 7.0000 / 7.0000 | 1.0000 / 1.0000 |
| p3 | PRIORITY | 3.6667 / 4.0000 | 7.0000 / 7.0000 | 1.0000 / 1.0000 |
| p4 | FCFS | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| p4 | PRIORITY | 0.0000 / 0.0000 | 0.0000 / 0.0000 | 0.0000 / 0.0000 |
| p5 | FCFS | 2.7500 / 2.7500 | 5.0000 / 5.0000 | 0.0000 / 0.0000 |
| p5 | PRIORITY | 1.5000 / 1.5000 | 3.0000 / 3.0000 | 0.0000 / 0.0000 |
| p6 | FCFS | 19.7500 / 24.9167 | 26.0000 / 49.0000 | 10.0000 / 7.0000 |
| p6 | PRIORITY | 20.1667 / 25.6667 | 23.0000 / 40.0000 | 7.0000 / 8.0000 |

P1 and P4 tie on the virtual waiting/churn measures. P2 has equal waiting
but fewer ORDERED rollbacks. P3 favors ROLLBACK on average waiting in this
snapshot. P5 shows no rollback under either policy; it does not demonstrate
starvation. P6 favors ROLLBACK on average and worst resource wait under both
schedulers. These observations support retaining ROLLBACK together with its
zero-held-while-waiting invariant; they do not establish a universal optimum.
Racing outcomes and wall times may vary on another run or machine.

P5 is finite. P6 is now a fixed-seed 12-reader/four-book stress example,
with balanced requests from every reader; regenerate it with the checked-in
seed-3710 script. Full spreads matter more than rounding a single timing.

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

`run_unsafe_demo()` uses separate tracers by default. With a supplied tracer,
the caller retains aggregate history but the engine starts a fresh event slice
for each run; each DemoReport exposes only its own result.trace. Existing
caller events therefore cannot contaminate later safety checks. Run from the
repository root in a source checkout; extracted archives now include the
relative default sample path too.

The optional `run_blocking_demo()` is callable from Python. It uses two actual
threads, a barrier, the same ResourceManager under NONE, and timed condition
waits. It has placeholder pool/timestamp statistics and records the configured
timeout as `wall_time_s`, not measured runtime. It is not a service/policy
benchmark. Its barrier and thread joins have no timeout protection.

## Evidence and remaining work

Current root discovery finds 173 tests: 172 pass and one missing-module check
is skipped because that module exists. All 54 A2 golden outputs match an
independent reference and repeated exports. New regressions failed before
the fixes and pass afterward. The measured policy run count is 720, with
independent trace safety checks enabled. Both archives now contain their
README, inputs, documentation, and applicable tests; the default packaged
deadlock demo and experiment commands are smoke-tested.

Real and fake memory satisfy the same behavior cases. Resource/worker fakes
retain their older limitations: NONE-style resource behavior regardless of
policy, and synchronous worker execution. Use real modules for policy tests.
Some old stress tests still do not establish global fairness or completion on
all inputs. Remaining trace provenance/order, CLI NONE validation, counter,
optional-demo and portability limitations are in the audit. Presentation
material and a timed viva rehearsal remain separate Final work.
