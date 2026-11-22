# Smart Library: OS Lab Assignment 1 (Python port)

A Python port of the group's C++ Assignment 1 (`../Assignment_1-OS_Lab_C++`).
Readers are processes, served by two identical librarians under **FCFS** or
**non-preemptive Priority Scheduling** in a discrete-event simulation with
integer virtual time.

A2 and the Final Project are written in Python, and they must keep A1's
behaviour. So this port reproduces the C++ program **byte for byte** on
the same input and algorithm. The modules follow the group's interface
contract (`../library_sim.pyi`), so A2 and the Final can reuse them
directly.

## Requirements

Python 3.10 or newer. Standard library only, no installation needed.

## Run

```bash
python3 main.py input.txt FCFS
python3 main.py input.txt PRIORITY
# equivalently:
python3 -m library_sim.a1 input.txt FCFS
```

```
python3 main.py INPUT_FILE ALGORITHM
```

- `INPUT_FILE`: the reader count N, the Round Robin quantum Q (read and
  validated but unused, because Library has no Round Robin), then N rows
  of `ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY`.
- `ALGORITHM`: `FCFS` or `PRIORITY` (uppercase).

The result is printed to stdout in the A1 machine-readable format, the same
as the C++ version:

```
PROCESS_ID,ARRIVAL,PRIORITY,SERVICE,START,COMPLETION,WAITING,TURNAROUND,RESPONSE
R1,0,3,7,0,7,0,7,0
...
SUMMARY
AVERAGE_WAITING,2.600000
AVERAGE_TURNAROUND,7.600000
AVERAGE_RESPONSE,2.600000
THROUGHPUT,0.384615
UTILIZATION,96.153846
```

Errors (wrong arguments, unknown algorithm, missing or malformed file) go
to stderr as `Error: ...`, with a line number where it applies. The exit
status is then 1 and nothing is printed to stdout.

## Code layout and mapping from C++

| C++ (`../Assignment_1-OS_Lab_C++/src`) | Python | Notes |
|---|---|---|
| `process.h` | `library_sim/models.py` | `ReaderSpec` (input row), `State` + legal transitions, `Reader`, `ReaderResult`, plus the shared constants and types A2/Final need |
| `input.h/.cpp` | `library_sim/a1.py`: `read_a1_input`, `parse_a1_text` | now validates input (see below) |
| `fcfs.h/.cpp` | `library_sim/a1.py`: `fcfs` | same algorithm |
| `priority.h/.cpp` | `library_sim/a1.py`: `priority_schedule` | same algorithm |
| (tie-break rules) | `library_sim/scheduler.py`: `fcfs_key`, `priority_key`, `ReadyQueue` | the keys are used by the A1 port. `ReadyQueue` is the event-driven queue the A2/Final engine uses |
| `metrics.h/.cpp` | `library_sim/metrics.py` | same formulas and the same floating-point operation order. Also computes the A2/Final fields (memory wait, ready wait, resource wait) |
| `output.h/.cpp` | `library_sim/output.py`: `format_a1` | same text, 6 decimals. `fmt_decimal` (4 decimals) is for A2/Final |
| `main.cpp` | `library_sim/a1.py`: `a1_main`, plus `main.py` | |
| — | `library_sim/errors.py` | `InputError`, `UsageError` |
| `tests/run_tests.sh` | `tests/run_tests.py` | |

## Algorithms (unchanged from the C++ version)

- **FCFS:** readers are sorted by arrival, with equal arrivals in
  lexicographic ID order. Each reader goes to the librarian who becomes
  free first (librarian 0 on ties). It starts at the later of that
  librarian's free time and its own arrival.
- **Priority (non-preemptive):** whenever a librarian becomes free (the
  earliest one, librarian 0 on ties), it serves the arrived reader with
  the smallest priority number. Ties go to the earlier arrival, then the
  lexicographically smaller ID. If nobody has arrived yet, the clock jumps
  to the next arrival.
- IDs compare as strings, so `R10` comes before `R2`.
- **Metrics:**
  - per reader: waiting = turnaround − service, turnaround = C − A,
    response = S − A
  - throughput = N / E
  - utilization = Σ service / (2 × E) × 100
  - E = last completion − first arrival

The algorithm comparison and analysis from the C++ README
(`../Assignment_1-OS_Lab_C++/README.md`) apply unchanged, because the
outputs are identical.

## Differences from the C++ version

On valid input there are none: the output is identical. Invalid input now
gets a clear error message where the C++ program crashed or misbehaved
(C++ README, "Known Limitations"). The parser rejects:
- an empty file
- N < 1, or Q missing or < 1
- fewer than N reader rows
- rows without 5 fields
- non-integer numbers
- empty, whitespace-containing or duplicate IDs
- ARRIVAL < 0, PRIORITY < 1 or SERVICE < 1
- an empty CATEGORY

Trailing blank lines and Windows (CRLF) line endings are accepted. As in
the C++ reader, CATEGORY is the rest of the row and lines after the N
reader rows are ignored.

## Tests

```bash
python3 tests/run_tests.py                  # 10 inputs x 2 algorithms vs tests/expected
python3 -m unittest discover -s tests -v    # regression + unit tests
```

- `tests/inputs` and `tests/expected` are copied unchanged from the C++
  project. Every expected file is reproduced byte for byte.
- `tests/test_a1.py` covers:
  - the same regression, both in-process and through the CLI
  - CLI error handling and every parser validation rule
  - lexicographic ID ordering, priority vs arrival, idle gaps
  - the `ReadyQueue`, lifecycle transitions and the A2-style metric fields
- Differential check: the Python port and the compiled C++ program were also
  run on 3000 random inputs × both algorithms, covering:
  - 1–25 readers
  - simultaneous arrivals and long gaps
  - service times up to 1000
  - IDs like `R10` vs `R2`

  All 6000 outputs were identical.
