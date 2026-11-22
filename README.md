# Smart Library — A1, A2, and Final

Group: **Kabir, Urvashi, Aarush, Samar**. Python 3.10+ and the standard library;
no virtual environment or package installation is required. The maintained
baseline is Python. The old C++ implementation is deprecated and is not needed.

| Stage | Library operation | OS concept |
|---|---|---|
| A1 | Two librarians serve readers using FCFS/Priority | Process scheduling |
| A2 | Readers reserve adjacent slots in a six-seat room | Contiguous allocation and FIFO admission |
| Final | Readers acquire/release named books and journals | Real threads, synchronization, deadlock prevention |

## Current implementation

Aarush A1–A7 (including A7b/A7c), A9, and A10 are implemented: real/fake
memory, 54 independently derived A2 golden exports, allocator/policy experiments,
measured comparisons, complete A2 README, and runnable archive assembly.
Optional A8 runtime visualization is not implemented.

Sam's parser/resource/worker/trace/deadlock modules are integrated. The audited
worker-overlap, shared-tracer isolation, and action-order/diagnostic defects
have regression fixes. The old unsupported policy-winner table is replaced
with 720 measured runs. ROLLBACK remains the safe default; other known Final
limits remain explicit in [the audit](docs/implementation_audit.md).

| Component | Owner | Status |
|---|---|---|
| Types, errors, Python A1, scheduler, parser, metrics, output | Kabir | Implemented; Python regressions pass |
| Seat allocation, FIFO admission, occupancy | Aarush | Implemented; shared tests exercise real and independent fake |
| Experiments, A2 examples/expected exports and comparison discussion | Aarush | Implemented; 6 allocator runs and 720 safe policy runs recorded |
| Engine, CLI, independent ZIP builder | Urvashi | Integrated; extracted archives run their tests/commands |
| Resources, real workers, tracing, policies, unsafe demo | Samar | Implemented with targeted fixes; remaining Final issues documented |

Validation snapshot on Python 3.12.3: **173 root tests, 172 passed and one
expected missing-module skip**; standalone A1 has 17 passing tests and 20/20
golden cases. Test counts describe this revision, not all future changes.

## Start here

- [A2 complete README](Assignment_2-OS_Lab_Python/README.md): architecture,
  input/export, metrics, six-way comparison, assumptions, and checklist.
- [Final implementation README](Final-OS_Lab_Python/README.md): real worker
  execution, policies, commands, measurements, and remaining limitations.
- [Standalone Python A1](Assignment_1-OS_Lab_Python/README.md).
- [Aarush guide and LaTeX/PDF](docs/aarush/README.md).
- [Sam's concurrency guide](docs/readme/samar_concurrency_deadlock.md).
- [Development guide](DEVELOPMENT.md), [task ownership](division_of_work.txt),
  and [interface contract](library_sim.pyi).

## Run and test

From the source repository root:

```bash
python3 -m unittest discover -s tests -t . -v
PYTHONPATH=src python3 -m library_sim.experiments allocators inputs/a2/comparison.txt
PYTHONPATH=src python3 -m library_sim.experiments policies inputs/policy/*.txt --repeats 30 --md policy-report.md
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import a2_main; raise SystemExit(a2_main(sys.argv[1:]))' inputs/a2/comparison.txt FCFS FIRST_FIT output.txt
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import final_main; raise SystemExit(final_main(sys.argv[1:]))' inputs/spec_sample.txt FCFS FIRST_FIT final-output.txt --trace trace.txt --stats
python3 build_packages.py
```

The build creates `dist/a2.zip` and `dist/final.zip`, extracts them, clears
source-path assistance, and verifies tests, six CLI combinations, allocator
experiments, and (Final) policy experiments and default deadlock demo. Both
archives include READMEs, documentation, inputs, and applicable tests. A2
excludes all five Final-only library modules. Extract either ZIP and use
`python3 main.py ...` from its directory; no build/install step is needed there.

## Evidence and design rules

[Manual fixture checks](docs/aarush/fixture_checks.md),
[full independent workbook](docs/aarush/fixture_derivations.md),
[allocator results](docs/aarush/allocator_comparison.md),
[policy spreads](docs/aarush/policy_comparison.md), and
[real overlap trace](docs/aarush/overlap_evidence.txt) support the implementation.
The policy JSON retains the measured snapshot and instrumentation; wall times
and racing Final outcomes can vary on reruns.

Only the coordinator mutates readers/ready/admission/seats; workers operate
through locked managers. No sleep or busy-wait drives simulation correctness.
Keep graded exports free of diagnostic prose. Preserve the interface contract,
run conformance and relevant regressions before sharing changes, and update
README/PDF claims from observations rather than expected winners.

The specification PDFs remain in the three stage directories. Earlier notes
referenced `context.md`; that file is absent, so the checked-in contracts and
PDFs are the available references. Historical TA-approval labels are not new
claims of independently verified approval.
