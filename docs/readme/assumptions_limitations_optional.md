<!-- Task G5 (owner: Kabir): DRAFT. Collect the remaining entries from each
     owner as their modules land, and remove each TODO once it is filled in. -->

## Assumptions

### Approved by the TA
1. START is the first dispatch to a librarian, even if the reader blocks
   on an ACQUIRE at offset 0. A ≤ M ≤ S always holds.
2. Event order at a timestamp t, repeated until nothing changes:
   1. resource actions due at t
   2. completions
   3. arrivals
   4. memory admission
   5. readers woken by releases become READY
   6. librarians are filled
   7. actions at offset 0 (or right after resuming) for readers just dispatched

   On release, a book is handed directly to the first eligible waiter.
3. A reader returning from `BLOCKED_RESOURCE` keeps its original arrival
   time in the scheduler key.
4. Peak occupancy and fragmentation are sampled once, at the end of each
   timestamp.
5. Resource-free Final runs still write the three CHECK lines (0, 0, N),
   with no RESOURCE lines. The A2 build never writes CHECK lines.
6. Decimal statistics have 4 decimal places. Percentages are percent values.

### Our own choices
- **Elapsed time E** runs from the first arrival to the last completion,
  as in A1.
- **Action order:** a reader's actions are stable-sorted by
  (WORK_OFFSET, row order). The spec already requires non-decreasing
  offsets per reader, so valid inputs are unaffected.
- **Deadlock prevention:** ROLLBACK and ORDERED are both implemented. The
  default is ROLLBACK, ensuring held_while_waiting == 0 and eliminating convoys
  when readers hold shared books during extended reading periods.
- **ORDERED** grants a free book in any order and only enforces the order
  when a reader would have to *wait*. That is enough to rule out circular
  wait.
- **No offset rewind:** a reader's work offset doesn't move back after a
  rollback (a modelling simplification).
- **RESOURCE lines** are written for every declared resource, even when
  K = 0 (the spec says "every declared shared resource").
- **Exit codes:** 0 for success; 1 for bad arguments or input (message on
  stderr, no output file); 2 for a Final run that ended with unfinished
  readers or deadlocks.
- **Input checks:** IDs are compared as strings, and numeric fields must
  be strict integers.
- TODO Aarush: allocator and admission assumptions.
- TODO Urvashi: engine assumptions.
- **Synchronization and worker-model (Samar):**
  - Worker threads run under real OS threads (ThreadPoolExecutor); all resource mutations are locked inside ResourceManager with atomic check-and-update.
  - Process lifecycle transitions remain confined strictly to the coordinator thread, keeping state changes completely race-free.
  - Waiters per resource are resolved in strict FIFO order via direct handoff on release, avoiding lost wake-ups and stealing.
  - Code avoids any reliance on GIL atomicity, making it thread-safe on free-threaded Python builds.

### Not applicable to the Library
The Final spec (section 11) asks for tests involving A1 preemption, Round
Robin quantum expiry and the Restaurant's TABLE pool. The Library uses
only non-preemptive FCFS and PRIORITY and has only the SPACE pool, so:
- no reader is ever preempted
- Q is read and validated, but never used
- TABLE_REQ must be 0

A reader that blocks on a book gives up its librarian voluntarily. That is
consistent with non-preemptive scheduling.

## Limitations
- PRIORITY has no aging, so low-priority readers can starve (shown in A1's
  `starvation.txt`).
- FIFO memory admission causes head-of-line blocking: a small request can
  wait behind a large one even when seats are free.
- A work offset doesn't rewind after a rollback.
- Racing thread events make the exact Final results vary between runs that
  have real contention. Resource-free baselines are deterministic.
- Python threads run under the GIL. That gives concurrency, not
  parallelism, but races are still possible, so every shared structure is
  protected by locks.
- TODO everyone: limitations from your own modules.

## Optional features
- `--trace` (resource-event log) and `--stats` (policy counters and wall
  time), both kept out of the graded output.
- An experiments harness: the allocator comparison and the ROLLBACK vs
  ORDERED comparison.
- `test_pyi_conformance`: checks automatically that the code matches the
  interface contract.
- TODO: memory map, blocking deadlock demo, anything else built.
