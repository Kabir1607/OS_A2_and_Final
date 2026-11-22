# Current remediation and delivery status

This section updates the historical audit below for base `8f256e6` plus the
A6/A7/A9/A10 working changes, validated on Python 3.12.3. The original findings
are preserved below as evidence of the pre-fix state, not current failures.

| Area | Current result |
|---|---|
| A6 | Eight edge cases + one comparison input; 54 complete golden exports, independent unit-time workbook, explicit hand-calculated anchors, repeated-output and conservation checks. |
| A7/A7b | Full contracted experiment API/CLI; six allocator rows; 24 policy cells × 30 = 720 safe, complete runs; Markdown spreads, per-metric comparisons, JSON instrumentation snapshot. |
| A7c | Independent fake memory and shared real/fake behavior checks. |
| A9/A10 | Memory discussion, Python A1 comparison, complete A2 README/checklist, current Final README, actual archive docs/samples/tests. |
| Worker overlap | Bounded barrier waves before resource locks; regressions assert distinct workers, positive interval overlap, waves, singles, contention, exceptions. Actual trace retained. |
| Shared traces | Each Simulation audits only its event slice; aggregate caller history remains intact. DemoReport.events matches result.trace. |
| Action validation | Descending per-reader offsets rejected before replay; semantic action errors use actual row numbers. |
| Policy claims | Unsupported predictions replaced by 720 measured runs; retain validated ROLLBACK, with documented workload-dependent trade-offs. |
| Archive checks | Both extracted suites, six CLI combinations, allocator command; Final also runs packaged demo and policy command. A2 has no five Final-only library modules. |

Baseline regressions reproduced four failures before edits: missing controlled
overlap, descending offsets accepted, incorrect semantic error line, and
cross-run trace contamination. They pass after corrections. Current root
suite has 173 tests (172 passed, one expected skip); standalone A1 retains
17 passing tests and 20/20 golden cases. No public interface signatures or
graded output formats changed.

[Manual anchors](aarush/fixture_checks.md), [independent workbook](aarush/fixture_derivations.md),
[allocator results](aarush/allocator_comparison.md), [policy results](aarush/policy_comparison.md),
[JSON](aarush/policy_results.json), and [overlap evidence](aarush/overlap_evidence.txt)
provide current evidence. Measurements include in-memory trace replay and
barrier coordination; they are not platform-independent timing guarantees.

Remaining outside the agreed four-issue/blocker scope: normal Final CLI still
accepts NONE; multi-resource handoff provenance/adjacency and early UNBLOCK
ordering differ from the contract; out-of-order counters are ORDERED-only;
optional blocking-demo statistics/timeouts remain limited; free-threaded/PyPy
portability and global fairness are unproven. Optional A8 and Final presentation
material are not completed. No claim of complete Final compliance is made.

---

## Historical pre-fix audit (code f69cd13)

# Implementation audit for Aarush and Samar's documentation

Audited on 22 November 2026 with Python 3.12.3 against code revision `f69cd13`.
This record supports corrections to documentation introduced by MushuRam01
(`a020c78`) and sam-b02 (`f69cd13`). It describes that revision; documenting
a defect does not fix it or change the interface contract.

## Code reviewed

| Area | Implemented behavior and audit finding |
|---|---|
| Types/errors | `models.py`, `errors.py`: reader records, six-seat/two-librarian defaults, enums, lifecycle checks, input/usage errors. |
| Python A1/scheduling | `a1.py`, `scheduler.py`: FCFS and non-preemptive Priority with string-ID tie-breaks. Six standalone implementation modules match shared copies; deprecated C++ is not needed. |
| Input | `parser.py` validates A2 rows and delegates Final sections lazily. `resource_parser.py` checks declarations and action replay, with ordering/diagnostic defects below. |
| Memory | `memory.py` implements Aarush A1–A4; A5 has 25 checks for functions, reservations, FIFO admission, statistics, and engine integration. |
| Coordination | `engine.py` owns virtual time, readers, queues, and seats; applies worker results; checks conservation for completed runs. Final wake events precede the contract's numbered step 5. |
| Metrics/output | `metrics.py` checks timestamps and waiting components. `output.py` emits six-decimal A1 summaries and four-decimal A2/Final statistics. Seat utilization is already a percentage before formatting. |
| Resources | `resources.py` locks ownership, waiters, counters, and resource-event calls; implements NONE, ROLLBACK, ORDERED. Fairness depends on eligibility/policy. |
| Workers/trace | `workers.py` uses real threads and batch intervals; overlap is detected when it occurs, not guaranteed. `trace.py` locks event recording; disabled tracers keep no history. |
| Deadlock | `deadlock.py` defines ranks/policies/counters, finds cycles, runs the real-engine demo when memory exists, and has a separate blocking demo with synthetic statistics. |
| CLI | `cli.py` provides A2/Final functions, trace/stats flags, demo delegation; normal Final also accepts NONE despite advertising safe policies only. |
| Fakes | Engine fake returns one fixed reader and ignores policy/scheduling; worker fake is sequential; resource fake accepts policy but uses NONE-style behavior. They do not prove policies/concurrency. No memory fake exists. |
| Packaging | `build_packages.py` excludes Final modules from A2 and builds runnable ZIPs; full READMEs, inputs, tests, and presentation material are omitted. |

All 51 Python files across shared code, standalone A1, repository tests, and
the builder parsed and compiled without writing bytecode. Syntax and interface
checks do not establish all behavioral requirements.

## Verification

| Check | Result and scope |
|---|---|
| Root unittest discovery | 134 found: 133 passed, 1 skipped. The skipped missing-module check now finds the Final module. |
| Standalone Python A1 | 17 tests passed; golden-output runner passed 20/20 cases. |
| Engine versus A1 | Existing test passes on 11 bundled + 200 seeded random workloads under both schedulers. Capacity equals all readers' total requests, so memory cannot delay admission. |
| Independent A2 reference | Earlier in this same revision audit, 200 workloads × 2 schedulers × 3 allocators matched a separate unit-time reference for timestamps and seat statistics: 1,200 comparisons; 1,200 reruns produced identical output. Temporary audit probes, not committed A6 fixtures. |
| Integrated Final | 10 bundled input files × 2 schedulers × 3 allocators × 2 safe policies × 3 repeats: 360 completed runs, no reported violations/deadlocks. Tracing was enabled for independent ownership replay. |
| Extracted archives | Both archives passed a hand-calculated resource-free case under all six combinations. A2 ran without the five Final-only modules. |
| Default unsafe demo | Fresh tracers per policy: NONE detects the R1/R2 cycle; both safe policies complete both readers with zero reported violations. |

Run committed checks from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t . -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.contract.test_pyi_conformance -v
```

From `Assignment_1-OS_Lab_Python`, run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
PYTHONDONTWRITEBYTECODE=1 python3 tests/run_tests.py
```

## Confirmed limitations and contract differences

1. **Normal-worker overlap is unproven.** In 100 fresh two-worker pools,
   two single-acquire batches used the same thread every time and recorded
   no overlap. The test named `test_real_threads_and_overlap` checks only
   name prefixes. This is an observation on this interpreter, not proof
   that overlap is impossible. Controlled distinct-thread evidence is pending.
2. **Shared demo traces contaminate audits.** Calling
   `run_unsafe_demo(tracer=Tracer())` retains unsafe holdings in later histories;
   both safe reports then show two false exclusivity violations. The default
   `run_unsafe_demo()` creates separate histories and avoids this problem.
3. **Action ordering/diagnostics are incomplete.** A reader's RELEASE at
   offset 5 followed in the file by ACQUIRE at offset 0 is accepted after
   sorting, despite the required non-decreasing input order. A semantic
   release-without-hold error on line 7 was reported against the R-count
   on line 4 instead of the action row.
4. **The normal CLI accepts NONE.** The unsafe sample with `--policy NONE`
   returns 2 and writes an incomplete report. Final writes output before
   testing `incomplete`, so not every nonzero exit means no output. Worker
   RuntimeErrors propagate and are not among the CLI's caught exceptions.
   An output-writing failure can leave a partial file.
5. **Handoff trace shape/provenance can be inaccurate.** ROLLBACK grants a
   whole waiting set after its last missing resource becomes free. Every
   HANDOFF uses the latest releasing reader in `from`, even for a book
   released earlier by someone else. Reproduced: R1 rolls back JOURNAL,
   then R2 releases REFERENCE_BOOK; both grants to R1 say `from R2`.
   Replay still reports zero ownership violations, but adjacency/provenance
   differ from CONTRACT 3. ORDERED likewise emits all rollback events
   before processing their handoffs.
6. **Final wake events happen early.** `_final_action_round` makes woken
   readers READY before completion/arrival/admission. A tested timestamp
   gave RELEASE → HANDOFF → UNBLOCK → COMPLETE → DISPATCH; the contract
   places wake processing after memory admission. This audit did not find
   a scheduling mismatch, but event order differs.
7. **Counters have comparison limits.** `out_of_order_requests` increments
   only under ORDERED. An uncontended REFERENCE_BOOK → JOURNAL sequence
   gives ORDERED=1, ROLLBACK=0. Resource `wait_events` counts acquires that
   return BLOCKED, not every internal ORDERED reacquisition wait. These
   counts are not resource-blocked durations.
8. **Portability and optional-demo claims need qualification.** Resource
   ownership locking does not assume GIL atomicity, but free-threaded Python
   and PyPy were not tested. `run_blocking_demo` has synthetic pool/timestamp
   statistics; `wall_time_s` is its supplied timeout. That parameter bounds
   condition waits, not arbitrary failures at its unbounded barrier/joins.
9. **Archives are executable but incomplete.** Both omit full READMEs and
   sample inputs. The extracted Final default deadlock demo exits 1 because
   `inputs/deadlock_unsafe.txt` is absent. The builder's resource-free smoke
   case does not prove Final concurrency/demo readiness.

## Policy sample evidence

`experiments.py` is absent. The former winner table was not backed by that
required harness. A focused P1 audit used FIRST_FIT and 30 repeats per cell:

| Scheduler | Policy | Runs | Rollbacks each run | Total resource wait each run | Last completion each run |
|---|---|---|---|---|---|
| FCFS | ROLLBACK | 30 | 0 | 5 | 11 |
| FCFS | ORDERED | 30 | 0 | 5 | 11 |
| PRIORITY | ROLLBACK | 30 | 0 | 5 | 11 |
| PRIORITY | ORDERED | 30 | 0 | 5 | 11 |

P1 ties on these metrics. This does not establish wall-time, fairness, or
P2–P6 winners. ROLLBACK is the current engineering default; measured default
selection is pending. Removing hold-and-wait does not eliminate every convoy
or prove starvation freedom.

P2–P6 are fixed candidate examples. P5 has one multi-book and three single-book
readers, not an unbounded stream. P6 is a fixed six-reader file; its last two
readers have no actions. It is not a random workload generator.

## Remaining deliverables

- A6: reusable A2 inputs and hand-verified expected outputs.
- A7/A7b: experiment harness and measured comparisons; A7c's memory fake.
- A9/A10: complete A2 README with results and archive assembly.
- Final: controlled overlap evidence, fixes/regressions for the above,
  full policy measurements/default selection, packaging and presentation.

Passing the recorded checks supports these observations; it is not proof
of correctness on every valid input or complete specification compliance.
