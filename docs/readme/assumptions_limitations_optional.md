<!-- G5 collection: corrected against code f69cd13 on 22 November 2026.
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

- ROLLBACK is the current default. Both safe policies exist, but a measured
  P1–P6 default selection is pending. Removing hold-and-wait does not prove
  the absence of every convoy or starvation case.
- Actions are sorted by work offset and row order. Descending input offsets
  are accepted despite the specification's ordering requirement.
- Offsets do not rewind after rollback. A woken reader has regained the
  resources required to resume before entering READY.
- NONE/ORDERED have per-resource FIFO queues. ROLLBACK selects the first
  globally queued waiter whose whole set is free, bypassing earlier
  ineligible requests. Neither OS lock fairness nor starvation freedom is assumed.
- Executor threads use locked ResourceManager/Tracer methods. Short batches
  need not overlap. Free-threaded Python and PyPy have not been verified.
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
- Final interleavings can change results. Controlled normal-worker overlap
  remains unproven; the current overlap test checks only thread-name prefixes.
- Shared tracers across unsafe-demo policies contaminate later replay checks.
  Use default separate histories until per-run isolation is implemented.
- Multi-resource handoff provenance/adjacency and early UNBLOCK events differ
  from the contract. Semantic action errors can identify the R-count line.
- Normal Final CLI currently accepts NONE despite advertising safe policies
  only. `out_of_order_requests` increments only under ORDERED.
- The optional blocking demo has synthetic simulation statistics; its timed
  condition waits do not bound arbitrary barrier/join failures.
- Passing bundled cases does not prove fairness, complete progress, or
  correctness for every input/runtime.
- Both archives run, but lack complete READMEs, sample/test files, and
  presentation material. The packaged default deadlock demo lacks its input.

## Implemented extensions and pending work

Implemented: optional `--trace`, `--stats`, `--quiet`; resource/policy counters;
cycle detection and the real-engine unsafe demo; a separate timed-wait blocking
demo; interface checks; and Aarush's function-by-function memory LaTeX/PDF guide.

Pending: A6 inputs/expected outputs, `experiments.py`, allocator and full policy
comparisons, measured default selection, a separate memory fake, runtime memory
maps/timelines, complete A2/Final READMEs/archive contents, and the documented
implementation fixes. Diagrams in the memory guide are explanatory examples,
not a runtime visualization feature.
