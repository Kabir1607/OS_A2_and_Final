# Smart Library — Assignment 2

Group: **Kabir, Urvashi, Aarush, Samar**. Python 3.10+; standard library only.
No virtual environment, package installation, compilation, or GUI is required.
This is the independent A1+A2 checkpoint; book synchronization is the Final project.

## Run the independent archive

From the source repository root, build with `python3 build_packages.py`.
Extract `dist/a2.zip` into a clean folder, open that folder, then run:

```bash
python3 main.py inputs/a2/comparison.txt FCFS FIRST_FIT output.txt
python3 main.py inputs/a2/comparison.txt PRIORITY BEST_FIT output.txt
python3 -m library_sim.experiments allocators inputs/a2/comparison.txt --md comparison.md
python3 -m unittest discover -s tests -t . -v
```

The archive contains its own `main.py`, package, input/expected-output files,
tests, contract, and documentation. It excludes resource_parser, trace,
resources, workers, and deadlock modules. The allocator experiments run with
those files absent. Policy comparison commands belong to the separate Final archive.

From the source checkout, the equivalent simulation command is:

```bash
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import a2_main; raise SystemExit(a2_main(sys.argv[1:]))' inputs/a2/comparison.txt FCFS FIRST_FIT output.txt
PYTHONPATH=src python3 -m library_sim.experiments allocators inputs/a2/comparison.txt
```

## Library and OS mapping

| Library entity/operation | OS model |
|---|---|
| Reader | Process |
| Two identical librarians | Two execution units |
| Service duration | CPU burst in integer virtual time |
| Six indexed reading seats | Fixed contiguous memory pool |
| Request for adjacent seats | Memory allocation |
| Line waiting for seats | BLOCKED_MEMORY admission queue |
| Seated reader waiting for a librarian | READY queue |
| Completion and returned seats | Termination and deallocation |

The request is an OS abstraction; one reader can reserve several slots.
No real-time sleep represents service. The coordinator jumps to the next
arrival or completion and owns all reader, queue, and seat state.

```text
Input -> parser -> engine coordinator
                     |-> FIFO admission -> SeatPool -> READY queue
                     |-> FCFS/Priority -> two librarians -> completion/release
                     |-> occupancy samples -> metrics -> exact CSV export
```

## Lifecycle, admission, and event order

Arrival joins one FIFO line; equal arrivals use lexicographic ID order
(R10 precedes R2). The head receives its entire contiguous reservation or
remains blocked. Later requests never bypass it, even if they fit. After
success, admission immediately retries the next head. Only admitted readers
become READY. Seats stay reserved while waiting for a librarian and during
service, until completion.

At time t: complete readers and release seats (ID order), register arrivals
(ID order), admit the fitting FIFO prefix, then fill free librarians (lower
index first). Repeat until stable; sample occupancy/fragmentation once.

FCFS chooses `(arrival, ID)`. Priority chooses `(priority, arrival, ID)`;
smaller priority numbers win. Both are non-preemptive. CATEGORY does not
change priority. No RR, SJF, TABLE pool, or service preemption is required.

## Allocation algorithms

First Fit takes the first fitting free run scanning from zero. Best Fit takes
the smallest fitting run; Worst Fit takes the largest. Equal-size ties choose
the lowest starting index, and placement starts there. Release clears exactly
the original block; adjacent free slots naturally become a single free run.
There is no compaction or alternate admission policy.

FIFO admission provides arrival-order fairness but can leave seats and a
librarian idle. Fragmentation can block a request despite sufficient total
free seats. First Fit is direct; Best Fit preserves larger holes but may
leave small remnants; Worst Fit leaves a larger remainder in its chosen hole
but consumes a large group. None is universally optimal.

## Input and export

Invocation: `python3 main.py INPUT FCFS|PRIORITY FIRST_FIT|BEST_FIT|WORST_FIT OUTPUT`.
Input is UTF-8: positive N, positive Q, then exactly N seven-field rows:

```text
ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY,SPACE_REQ,TABLE_REQ
```

Use unique, nonempty whitespace-free IDs; arrival >=0; priority/service >=1;
nonempty comma-free category; SPACE_REQ 1–6; TABLE_REQ 0. Rows may be unordered.
Q is validated but unused. Trailing blanks, surrounding field whitespace,
CRLF, and a UTF-8 BOM are accepted. Resource sections are rejected in A2.
Handled input/usage errors print `Error:` to stderr and return 1 before
result writing; success returns 0. A filesystem writing error can leave a
partial file; writing is not transactional.

Output has no header or prose. PROCESS rows are sorted by string ID:

```text
PROCESS,ID,ARRIVAL,PRIORITY,SERVICE,START,COMPLETION,WAITING,TURNAROUND,RESPONSE,MEM_ADMIT,MEM_WAIT,READY_WAIT
SUMMARY,AVERAGE_WAITING,value
SUMMARY,AVERAGE_TURNAROUND,value
SUMMARY,AVERAGE_RESPONSE,value
SUMMARY,THROUGHPUT,value
SUMMARY,SERVICE_UTILIZATION_PCT,value
SUMMARY,AVERAGE_MEMORY_WAIT,value
SUMMARY,COMPLETED_COUNT,value
SUMMARY,BLOCKED_FOR_MEMORY_COUNT,value
POOL,SPACE,6,PEAK_OCCUPIED,UTILIZATION_PCT,MAX_EXT_FRAG_SLOTS
```

The capitalized column names above are placeholders, not an exported header.
Files use UTF-8/LF; times/counts are integers and decimal statistics use four
places. A2 writes no RESOURCE or CHECK lines.

## Metrics

A=arrival, M=memory admission, S=first start, C=completion, B=service:
turnaround=C−A; response=S−A; waiting=C−A−B; memory wait=M−A;
ready wait=waiting−memory wait. With E=max C−min A, throughput=N/E and
librarian utilization=sum B/(2E)×100. Blocked-for-memory count means M>A.

Seat utilization is occupied seat-time/(6E)×100, including reservations of
READY readers. Peak and maximum external fragmentation are sampled after
all processing at each timestamp. Fragmentation=total free−largest free run;
empty/full pools have zero. Percentages are already multiplied by 100
before formatting. [Function guide](../docs/aarush/memory_management.pdf).

## Six-way measured comparison

Input: `inputs/a2/comparison.txt`, ten readers; capacity six. All choices
complete ten readers, block three for memory, and reach a peak of six seats.

| Scheduler | Allocator | Avg wait | Avg turnaround | Avg response | Throughput | Librarian % | Avg memory wait | Seat % | Max fragmentation | Last completion |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| FCFS | FIRST_FIT | 5.5000 | 11.8000 | 5.5000 | 0.3030 | 95.4545 | 0.9000 | 69.1919 | 2 | 35 |
| FCFS | BEST_FIT | 5.5000 | 11.8000 | 5.5000 | 0.3030 | 95.4545 | 0.9000 | 69.1919 | 0 | 35 |
| FCFS | WORST_FIT | 5.5000 | 11.8000 | 5.5000 | 0.3030 | 95.4545 | 0.9000 | 69.1919 | 1 | 35 |
| PRIORITY | FIRST_FIT | 5.9000 | 12.2000 | 5.9000 | 0.2857 | 90.0000 | 1.2000 | 63.3333 | 2 | 37 |
| PRIORITY | BEST_FIT | 5.9000 | 12.2000 | 5.9000 | 0.2857 | 90.0000 | 1.2000 | 63.3333 | 1 | 37 |
| PRIORITY | WORST_FIT | 5.9000 | 12.2000 | 5.9000 | 0.2857 | 90.0000 | 1.1000 | 64.2857 | 1 | 37 |

At t=5, holes 0–2 and 4–5 surround R05 at seat 3. R04 needs two seats;
Best Fit takes 4–5, First/Worst Fit take 0–1. R08 and R01 then choose different
single seats. Under FCFS this changes fragmentation but not service/admission
order. Under Priority, Worst Fit admits R02 at 12 instead of 13 after R08
finishes. R02 still starts at 13, exchanging one unit of memory wait for
ready wait; completion order is unchanged.

For these readers Python A1 has the same total-wait/throughput/librarian
numbers and completions, with memory waiting zero. A2 changes waiting
components and seat usage without necessarily changing service timings.
The separate HOL fixture does change service availability: a smaller reader
waits behind a blocked head while a librarian can be idle.

[Independent arithmetic and placement examples](../docs/aarush/fixture_checks.md),
[all timestamp/seat derivations](../docs/aarush/fixture_derivations.md), and
[generated comparison table](../docs/aarush/allocator_comparison.md) provide evidence.

## Tests, assumptions, and limitations

Eight small edge cases plus the comparison workload have 54 golden exports.
They cover simultaneous arrivals/completions, initial/long idle periods,
FIFO blocking, size 1/6, fragmented requests, exact fits, equal holes, and
coalescing. Golden values come from a test-only independent unit-time oracle
and explicit manual anchors, not production simulator output. Real/fake
memory use the same contract cases. The engine is also cross-checked against
Python A1 with enough capacity for every reader simultaneously.

Priority has no aging; FIFO can reduce utilization; compaction and runtime
memory maps are absent. Larger pool capacity is a testing facility, not a
standard input option. The source includes LaTeX/PDF documentation and a
repeatable experiments command. Final-only bugs do not change A2 semantics.

## A2 specification checklist

- [x] Library's A1 FCFS/Priority and two execution units retained.
- [x] All three contiguous allocation algorithms and deterministic ties.
- [x] Integrated admission, reservation lifetime, service, and release.
- [x] Required input, output, scheduling and memory metrics.
- [x] Repeated-output determinism and edge-case examples.
- [x] Six-way measured comparison and fairness/utilization discussion.
- [x] README, independent archive, and clean-directory run/test checks.

The build script verifies archive execution before reporting success. The
separate Final archive additionally carries resource/policy examples and its
own status README; it is not required to run this A2 checkpoint.
