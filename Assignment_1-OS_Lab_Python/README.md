# Smart Library — Assignment 1 Python baseline

Group: Kabir, Urvashi, Aarush, Samar. Python 3.10+ and the standard library.
The C++ predecessor is deprecated and not required. Readers are processes,
served by two identical librarians using FCFS or non-preemptive Priority.
Service is integer virtual time; the simulator never sleeps to represent it.

From this directory:

```bash
python3 main.py input.txt FCFS
python3 main.py input.txt PRIORITY
python3 -m unittest discover -s tests -v
python3 tests/run_tests.py
```

CLI: `python3 main.py INPUT_FILE FCFS|PRIORITY`. Input is N, positive Q,
then N records `ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY`. Arrival is nonnegative;
service/priority positive; IDs unique. Category is descriptive. Q is validated
but unused. A1 preserves its legacy parser behavior: category is the rest of
the row and extra rows after N are ignored; numeric parsing uses Python int.
A2/Final use their stricter seven-field parser instead. Invalid/missing input
or bad arguments return 1, with `Error:` on stderr and no normal stdout report.

## Scheduling and lifecycle

Readers move NEW → READY → RUNNING → TERMINATED conceptually; the A1 port
computes the resulting timestamps directly. FCFS chooses arrival then string
ID. Priority chooses smaller priority number, then arrival, then ID. R10 sorts
before R2. Running readers are never preempted by later higher-priority arrivals.
Each dispatch uses the earliest available librarian, librarian 0 on ties.
No memory allocation, books, threads, RR, or preemption are needed for A1.

The package separates models, scheduler, metrics, formatter, errors, and the
A1 parser/runner. Six implementation modules are shared copies of the current
`src/library_sim` foundation; the tests compare bundled golden outputs without
requiring a C++ executable or directory.

## Output and metrics

Output begins with
`PROCESS_ID,ARRIVAL,PRIORITY,SERVICE,START,COMPLETION,WAITING,TURNAROUND,RESPONSE`,
then reader rows sorted by ID, then SUMMARY and five named values:
AVERAGE_WAITING, AVERAGE_TURNAROUND, AVERAGE_RESPONSE, THROUGHPUT, UTILIZATION.
Summaries retain six decimal places.

For A=arrival, S=first start, C=completion, B=service: turnaround=C−A,
response=S−A, waiting=C−A−B. With E=last completion−first arrival,
throughput=N/E and utilization=sum B/(2E)×100. Initial time before the first
arrival is excluded; idle gaps inside the observation window are included.

## Measured scheduler comparison

On `tests/inputs/spec_sample.txt`:

| Scheduler | Average waiting | Average turnaround | Average response | Throughput | Librarian utilization % | Last completion |
|---|---:|---:|---:|---:|---:|---:|
| FCFS | 2.600000 | 7.600000 | 2.600000 | 0.384615 | 96.153846 | 13 |
| PRIORITY | 2.200000 | 7.200000 | 2.200000 | 0.384615 | 96.153846 | 13 |

Priority serves R5 at 5 rather than 10, ahead of lower-priority R3. R3 starts
at 8 rather than 5. It improves averages here without changing final elapsed
time or busy work, so throughput/utilization tie. This does not make Priority
universally superior: it has no aging and can repeatedly delay low-priority
readers. `starvation.txt` demonstrates finite postponement, not an infinite
execution. FCFS preserves arrival-order service but can keep short readers
behind long ones.

## Validation and limitations

The standalone suite has 17 tests and the golden runner checks 10 inputs ×
2 algorithms = 20 output files. Cases cover one reader, ties, simultaneous
arrivals, arrivals during service, long/short service, idle gaps, and priority
postponement. Claims of old C++ differential runs are historical; the current
verification uses the checked-in Python fixtures.

The project adds no A1 optional scheduler or aging feature. This directory
is independently runnable. See the A2 README for six-seat admission and
memory metrics, and the separate Final README for shared-resource work.
