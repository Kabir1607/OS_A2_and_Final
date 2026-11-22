<!-- G5 collection: updated after A6/A7 and targeted Sam fixes on 22 November 2026.
     Draft contribution to the eventual submission READMEs. -->

## Assumptions and implemented behavior

See the [implementation audit](../implementation_audit.md) for reviewed code,
verification, and reproduced issues. Recorded contract decisions and current
implementation differences are distinguished below.

### Recorded project decisions

The contract and earlier notes describe these decisions as TA-approved.
This audit checked code, not external approval history; the referenced
`context.md` is absent from this checkout.

1. START is first dispatch, including an ACQUIRE blocked at offset zero.
2. Intended Final timestamp order: resource actions → completions → arrivals
   → memory admission → wake processing → dispatch → newly enabled actions,
   repeated until stable. The engine currently makes woken readers READY
   inside the action round, before completions/arrivals. Dispatch follows
   admission. A2 uses completions → arrivals → admission → dispatch.
3. Woken readers retain their original arrival in scheduler keys.
4. Occupancy/fragmentation are sampled once after each timestamp finishes.
5. Resource-free Final appends RESOURCE_WAIT=0 and CHECK values 0/0/N.
   A2 emits neither RESOURCE nor CHECK lines.
6. A2/Final statistics use four decimal places. Percentages already include
   multiplication by 100 before formatting. A1 retains six-decimal summaries.

### Memory and scheduling

- Standard runs use two librarians and six seats. Configurable pool capacity
  is for tests; input parsing still restricts SPACE_REQ to 1–6.
- First/Best/Worst Fit place at the selected run's lowest index; equal-size
  Best/Worst Fit candidates choose the lowest index. No compaction occurs.
- Memory admission is strict FIFO, including head-of-line blocking. The
  engine supplies arrival/string-ID order. Seats remain reserved through
  ready waiting, service, and resource blocking until completion.
- Readers, ready/admission queues, and SeatPool belong to the coordinator.
  Memory classes do not set lifecycle state or timestamps.
- For completed runs, E is last completion minus first arrival. Seat
  utilization is occupied seat-time / (capacity × E) × 100. Empty or
  zero-duration tracker reports return zero utilization.

### Resources, workers, and reporting

- ROLLBACK is retained after 720 safe P1–P6 runs; both policies remain selectable.
  Results support its average/worst resource-wait trade-off on the fixed P6
  case and zero held-while-waiting. No universal optimum or starvation freedom
  is claimed; consult the full measured spreads.
- Per-reader work offsets are checked in input order before ownership replay.
  Descending offsets are rejected; equal-offset row order is preserved. Semantic
  action errors carry the actual input action line.
- Offsets do not rewind after rollback. A woken reader has regained the
  resources required to resume before entering READY.
- NONE/ORDERED have per-resource FIFO queues. ROLLBACK selects the first
  globally queued waiter whose whole set is free, bypassing earlier
  ineligible requests. Neither OS lock fairness nor starvation freedom is assumed.
- Executor waves meet at a bounded barrier before resource operations, ensuring
  controlled overlap for multiple batches/workers. Single batches/workers skip
  the barrier. Ownership checks/updates are locked. Free-threaded Python and
  PyPy have not been verified.
- RESOURCE lines include every declared resource, even when K is zero.
  Disabled tracing retains no independent ownership replay history.
- CLI statuses: 0 for completion; 1 for handled input/usage/I/O errors;
  2 for incomplete Final execution. Final writes its report before returning
  2. Worker RuntimeErrors propagate. Output-writing failures can leave
  partial files, so not all failures imply no output file.

### Not applicable to the Library

Only non-preemptive FCFS and Priority are required. Round Robin, scheduler
preemption, quantum expiry, and the Restaurant TABLE pool are not required.
Q is validated but unused and TABLE_REQ is zero. Resource blocking releases
a librarian voluntarily while retaining seats. A policy rollback of books
is distinct from preempting service.

## Limitations

- Priority has no aging. Finite examples show delayed low-priority service;
  an ongoing higher-priority stream could cause starvation.
- FIFO admission can leave seats idle behind an unfitting head. Scattered
  free seats cannot satisfy a larger contiguous request.
- Final interleavings and wall times can change across runs. Controlled overlap
  is tested; that does not make thread winners deterministic or prove fairness.
- Sequential shared tracers retain aggregate history, but each simulation audits
  its own event slice. Concurrent simulations sharing one tracer are not a
  validated use case.
- Multi-resource handoff provenance/adjacency and early UNBLOCK events still
  differ from the contract; those unrelated audit issues remain open.
- Normal Final CLI currently accepts NONE despite advertising safe policies
  only. `out_of_order_requests` increments only under ORDERED.
- The optional blocking demo has synthetic simulation statistics; its timed
  condition waits do not bound arbitrary barrier/join failures.
- Passing bundled cases does not prove fairness, complete progress, or
  correctness for every input/runtime.
- Both archives now include actual READMEs, samples and applicable tests; the
  packaged default demo runs. Presentation slides and viva rehearsal remain
  separate Final deliverables.

## Implemented extensions and pending work

Implemented: optional `--trace`, `--stats`, `--quiet`; resource/policy counters;
cycle detection and the real-engine unsafe demo; a separate timed-wait blocking
demo; interface checks; and Aarush's function-by-function memory LaTeX/PDF guide.

Implemented in this follow-up: eight A6 fixtures plus the A7 comparison input,
54 independently derived golden exports, the full experiment harness and 720-run
policy report, a memory fake checked by shared contracts, A9/A10 READMEs, archive
assembly/verification, and the listed worker/tracer/parser regressions.

Pending: optional A8 runtime maps/timelines and the remaining Final trace,
CLI, counter, optional-demo and portability issues recorded in the audit.
Documentation diagrams are examples, not a runtime visualization feature.
