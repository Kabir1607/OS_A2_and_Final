<!-- README sections for task K11 (Kabir). Used in both the A2 and the Final README. -->

## Retained A1 scheduling algorithms

The Library uses two non-preemptive schedulers with two identical
librarians. When both librarians are idle at the same time, the
lower-numbered one is filled first.

| Scheduler | Next reader chosen by (`scheduler.py`) |
|---|---|
| `FCFS` | earliest arrival, then lexicographically smaller ID: `(arrival, id)` |
| `PRIORITY` | smaller priority number, then earlier arrival, then smaller ID: `(priority, arrival, id)` |

- IDs compare as strings, so `R10` comes before `R2`.
- A reader that has started is never interrupted: there is no preemption
  and no Round Robin. Q is read and validated, but unused.
- READY readers sit in a heap ordered by that key (`ReadyQueue`).
- In the Final Project, a reader returning from `BLOCKED_RESOURCE` keeps
  its original arrival time in the key (TA-approved), so it doesn't lose
  its place.

The schedulers are the A1 ones, unchanged. The Python port of A1
(`Assignment_1-OS_Lab_Python`) reproduces the C++ A1 output byte for byte:
- on all 20 A1 test cases
- on 6000 random runs compared directly with the compiled C++ program

## Metrics

For reader *i*: A = arrival, M = memory admission, S = first start, C =
completion, B = service.

| Metric | Definition |
|---|---|
| TURNAROUND | C − A |
| RESPONSE | S − A. S is the first dispatch to a librarian, even if the reader then blocks on a book at offset 0 (TA-approved) |
| WAITING | C − A − B |
| MEM_WAIT | M − A |
| RESOURCE_WAIT | total virtual time spent in `BLOCKED_RESOURCE` (0 in A2 and in resource-free runs) |
| READY_WAIT | WAITING − MEM_WAIT − RESOURCE_WAIT |

So WAITING = MEM_WAIT + READY_WAIT + RESOURCE_WAIT always holds.
`compute_process_metrics` checks it, together with A ≤ M ≤ S ≤ C.

With E = max C − min A:
- THROUGHPUT = N / E
- SERVICE_UTILIZATION_PCT = ΣB / (2E) × 100
- AVERAGE_MEMORY_WAIT = mean MEM_WAIT
- BLOCKED_FOR_MEMORY_COUNT = number of readers with M > A (they didn't
  get their seats on arrival)

ΣB is the librarians' total busy time, because a reader only holds a
librarian while it is being served. Waiting for memory or a book uses no
librarian. E starts at the first arrival, the same window as throughput
and as in A1.

## Output formats

- One UTF-8 file with `\n` line endings, comma-separated, no header row
  and no debug text.
- PROCESS lines are sorted by ascending ID.
- **A2:** PROCESS lines, then the 8 SUMMARY lines in spec order, then
  `POOL,SPACE,6,...`.
- **Final:** the A2 PROCESS lines with `RESOURCE_WAIT` appended, the same
  SUMMARY and POOL lines, then:
  - one `RESOURCE` line per declared resource, sorted by ID
  - `CHECK,EXCLUSIVITY_VIOLATIONS`, `CHECK,UNRESOLVED_DEADLOCKS`,
    `CHECK,COMPLETED_COUNT`
- **Resource-free input in Final mode:** the same numbers as A2, with
  `RESOURCE_WAIT` = 0 and no RESOURCE lines. The CHECK lines are still
  written: 0, 0, N (TA-approved).
- Times and counts are integers.

## Decimal precision

- **A2 and Final:** every decimal statistic uses exactly 4 decimal places
  (`3.6667`, `75.0000`). Percentages are percent values, not fractions.
  Rounding to 4 places stays well within the 10⁻³ tolerance; 2 places
  could exceed it. `-0.0000` is never printed, and non-finite values raise
  an error instead of being written.
- **A1:** keeps its original 6 decimal places, so it matches the C++ output.

## Input validation

Malformed input never hangs or crashes. It produces
`Error: line N: <reason>` on stderr, exit status 1, and no output file.

| What is checked | Rule |
|---|---|
| file | readable UTF-8 (a byte-order mark is accepted) |
| N, Q | integers ≥ 1 |
| reader rows | exactly N, each with 7 fields |
| numbers | strict integers: `2.5`, `1_0` and empty fields are rejected |
| IDs | unique, non-empty, no whitespace |
| ARRIVAL | ≥ 0 |
| PRIORITY, SERVICE | ≥ 1 |
| CATEGORY | non-empty |
| SPACE_REQ | 1–6 |
| TABLE_REQ | 0 |

Trailing blank lines and CRLF line endings are accepted. In A2 mode,
anything after the reader rows is an error. In Final mode it is parsed as
the resource and action sections.
