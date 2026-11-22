# Smart Library — an integrated OS simulator (CS-3710)

A library where **readers** queue for **reading seats**, are served by two
**librarians**, and share named **books and journals**. Behind it are the
three core operating-systems problems:

| Question | Stage | OS concept | What we built |
|---|---|---|---|
| *Who should be served next?* | **A1** Process management | CPU scheduling | FCFS and non-preemptive PRIORITY over two librarians |
| *Where can the reader sit?* | **A2** Memory management | Contiguous allocation | First, Best and Worst Fit over 6 adjacent seats, strict FIFO admission, fragmentation |
| *How can readers safely share books?* | **Final** Concurrency | Threads, locks, deadlock | Real worker threads, lock-protected ownership, ROLLBACK and ORDERED deadlock prevention |

Each stage keeps everything from the stage before it. The Final program
runs one integrated pipeline for every reader: arrival → seat admission →
librarian scheduling → book acquire/block/release → completion. The
simulation clock is virtual, but the book operations run on **real OS
threads** under real locks.

**Group:** Kabir, Urvashi, Aarush, Samar · **Language:** Python 3.10+,
standard library only (no installs, no build step)

---

## Stage READMEs

| Stage | README | Contents |
|---|---|---|
| **Final Project** | [Final-OS_Lab_Python/README.md](Final-OS_Lab_Python/README.md) | The full submission README: architecture, threads and synchronization, deadlock demo and prevention, measured results, trade-offs, assumptions, requirements checklist |
| **Assignment 2** | [Assignment_2-OS_Lab_Python/README.md](Assignment_2-OS_Lab_Python/README.md) | Seat allocation, FIFO admission, metrics, six-way allocator comparison |
| **Assignment 1** | [Assignment_1-OS_Lab_Python/README.md](Assignment_1-OS_Lab_Python/README.md) | Standalone Python A1 (the scheduling simulator) |

Each folder also holds that stage's specification PDF.

---

## Quick start

Everything runs from the repository root. The package lives in `src/`, so
add it to the path:

```bash
# Run all tests (173)
python3 -m unittest discover -s tests -t . -v

# Final: the spec's sample workload with contention, plus trace and statistics
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import final_main; raise SystemExit(final_main(sys.argv[1:]))' \
    inputs/spec_sample.txt FCFS FIRST_FIT output.txt --trace - --stats

# Final: bounded deadlock demo (NONE deadlocks; ROLLBACK and ORDERED complete)
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import final_main; raise SystemExit(final_main(sys.argv[1:]))' --demo-deadlock

# A2: allocation run
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import a2_main; raise SystemExit(a2_main(sys.argv[1:]))' \
    inputs/a2/comparison.txt PRIORITY BEST_FIT output.txt

# Comparisons
PYTHONPATH=src python3 -m library_sim.experiments allocators inputs/a2/comparison.txt
PYTHONPATH=src python3 -m library_sim.experiments policies inputs/policy/*.txt --repeats 30 --md policy-report.md

# Build the two submission archives
python3 build_packages.py
```

`build_packages.py` writes **`dist/a2.zip`** and **`dist/final.zip`**, the two
independent submissions. Each unzipped archive has its own `main.py`, so
you run it as:

```bash
python3 main.py INPUT_FILE {FCFS|PRIORITY} {FIRST_FIT|BEST_FIT|WORST_FIT} OUTPUT_FILE   # plus Final options
```

**Build checks.** The script unzips each archive into a clean folder and
checks it there with a plain `python3`:
- the test suite;
- all six scheduler × allocator combinations;
- the experiments;
- for Final, the deadlock demo.

The A2 archive contains none of the five Final-only modules.

---

## What the output looks like

The spec's two-reader sample (`inputs/spec_sample.txt`). Both readers race
for `REFERENCE_BOOK` on two worker threads:

```text
PROCESS,R1,0,1,6,0,11,5,11,0,0,0,0,5
PROCESS,R2,0,3,6,0,6,0,6,0,0,0,0,0
SUMMARY,AVERAGE_WAITING,2.5000
...
POOL,SPACE,6,2,25.7576,0
RESOURCE,JOURNAL,1,1,2,0
RESOURCE,REFERENCE_BOOK,1,1,2,1
CHECK,EXCLUSIVITY_VIOLATIONS,0
CHECK,UNRESOLVED_DEADLOCKS,0
CHECK,COMPLETED_COUNT,2
```

The trace (`--trace -`) shows which thread did what, at what virtual time:

```text
[t=0 #9 worker-2] R2 ACQUIRE REFERENCE_BOOK
[t=0 #10 worker-1] R1 BLOCK REFERENCE_BOOK (held by R2)
[overlap] worker-1 [...] and worker-2 [...] in real execution
[t=5 #14 worker-2] R1 HANDOFF REFERENCE_BOOK (from R2)
[t=5 #15 MainThread] R1 UNBLOCK
```

---

## Key results

- **Allocators** (`inputs/a2/comparison.txt`, FCFS): maximum external
  fragmentation is 2 for First Fit, 0 for Best Fit and 1 for Worst Fit.
  PRIORITY raises average waiting from 5.50 to 5.90 compared with FCFS.
- **Deadlock prevention:** 720 measured runs (6 workloads × 2 schedulers ×
  2 policies × 30). All completed, with 0 exclusivity violations and
  0 deadlocks.
  - On the 12-reader stress workload, the default **ROLLBACK** policy had
    about 20 % lower average waiting than ORDERED.
  - It had roughly half the worst-case resource wait.
  - It never held a book while waiting.
- **Correctness evidence:**
  - With no seat limit, the engine reproduces A1 exactly on 211 inputs.
  - All 54 hand-checked A2 expected outputs are reproduced byte for byte.
  - Resource-free Final runs equal A2 exactly.
  - Random stress runs found no violation, deadlock or hang.

Details and full tables:
[Final README §13–14](Final-OS_Lab_Python/README.md#13-observed-comparison-results),
[allocator results](docs/aarush/allocator_comparison.md),
[policy results](docs/aarush/policy_comparison.md).

---

## Repository layout

```text
src/library_sim/              the shared Python package used by A2 and Final
  models.py, errors.py          types, lifecycle, constants
  parser.py, resource_parser.py input validation (A2 section, then R/K sections)
  scheduler.py                  FCFS / PRIORITY ready queue
  memory.py                     SeatPool (First/Best/Worst Fit), FIFO admission, occupancy
  engine.py                     discrete-event coordinator: virtual clock, event order
  workers.py                    real worker threads (ThreadPoolExecutor)
  resources.py                  lock-protected book ownership and prevention policies
  deadlock.py                   policies, ranks, cycle detection, bounded unsafe demo
  trace.py                      thread-safe event trace and exclusivity replay
  metrics.py, output.py         metrics and the exact output format
  cli.py, experiments.py        command line, comparison tool
  a1.py                         Python A1 port (reference for regression tests)
library_sim.pyi               interface contract every module is tested against
inputs/                       spec sample, deadlock/integration demos, a2/ edge cases, policy/ workloads
tests/                        contract/ (per module), integration/, fakes/, expected/a2/ golden outputs
docs/                         per-member guides, measurements, implementation audit, memory-management PDF
Assignment_1-OS_Lab_Python/   standalone A1 (Python port, 20/20 golden cases)
Assignment_1-OS_Lab_C++/      original C++ A1 (deprecated; kept for reference)
Assignment_2-OS_Lab_Python/   A2 README and specification
Final-OS_Lab_Python/          Final README and specification
build_packages.py             builds and checks dist/a2.zip and dist/final.zip
```

---

## Team

| Member | Responsibility |
|---|---|
| **Kabir** | Python A1 port; shared models, scheduler, parser, metrics, output; interface contract |
| **Aarush** | Seat allocation and FIFO admission; experiments; A2 edge cases and expected outputs; A2 README |
| **Urvashi** | Simulation engine, command line, packaging, integration |
| **Samar** | Resource parsing, worker threads, resource manager, tracing, deadlock prevention and demo |

More detail: [development guide](DEVELOPMENT.md),
[division of work](division_of_work.txt), and the
[implementation audit](docs/implementation_audit.md), which lists known
limitations.
