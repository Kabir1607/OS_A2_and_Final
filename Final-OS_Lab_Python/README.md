# Smart Library — Final implementation snapshot

Group: Kabir, Urvashi, Aarush, Samar. Python 3.10+; standard library only.
Build from the source repository with `python3 build_packages.py`, extract
`dist/final.zip`, and run from the extracted folder:

```bash
python3 main.py inputs/spec_sample.txt FCFS FIRST_FIT output.txt --policy ROLLBACK --trace trace.txt --stats
python3 main.py inputs/a2/comparison.txt PRIORITY BEST_FIT baseline.txt
python3 main.py --demo-deadlock
python3 -m library_sim.experiments policies inputs/policy/*.txt --repeats 30 --md policy-report.md
python3 -m library_sim.experiments allocators inputs/a2/comparison.txt --md allocator-report.md
python3 -m unittest discover -s tests -t . -v
```

In the source checkout use `PYTHONPATH=src python3 -m library_sim.experiments`
and the root README's CLI adapter. Normal simulations default to ROLLBACK;
ORDERED is also selectable. NONE is intended for the bounded unsafe demo,
although the normal CLI still accepts it (a documented remaining limitation).

## Integration and output

The coordinator owns integer virtual time, readers, seats, FIFO admission,
and FCFS/Priority scheduling on two librarians. Real worker threads execute
book/journal actions under ResourceManager's lock. A blocked reader gives up
its librarian but keeps its seats. A granted wait returns it to READY without
rerunning the blocked ACQUIRE. Work offsets do not rewind after rollback.

Input starts with the seven-field A2 reader rows, then optionally R named
capacity-one resources and K rows of `ID,WORK_OFFSET,ACTION,RESOURCE_ID,UNITS`.
Offsets must be non-decreasing within a reader; equal offsets preserve row
order. Every acquire needs a release, including releases at SERVICE.

Final output is A2 PROCESS/SUMMARY/POOL with RESOURCE_WAIT appended to each
PROCESS, a RESOURCE line for every declaration, then CHECK exclusivity,
unresolved deadlocks, and completed count. Decimal fields use four places.
WAITING = MEM_WAIT + READY_WAIT + RESOURCE_WAIT. Resource-free runs retain
A2 numeric results with RESOURCE_WAIT=0 and CHECK 0/0/N. Trace/stats are
outside graded output. Incomplete Final runs write a report and exit 2;
handled usage/input errors return 1. Writing itself is not transactional.

## Policy evidence and fixes

ROLLBACK releases all holdings before waiting for an atomic complete set,
breaking hold-and-wait. ORDERED releases higher-ranked holdings on a backward
wait, then reacquires ascending resources, targeting circular wait. A free
book can be granted in any order. Eligibility-based queues are not a global
fairness or starvation-freedom guarantee.

The 720-run comparison (six inputs × two schedulers × two policies × 30)
completed safely. [Full spreads and per-metric comparisons](../docs/aarush/policy_comparison.md)
and [machine-readable measurements](../docs/aarush/policy_results.json) retain
results and instrumentation. Wall times include ownership tracing and the
same worker barriers for both policies and can vary by machine.

ROLLBACK remains the engineering default. On this measured P6 workload it
has lower average/worst resource waiting under both schedulers, while ORDERED
can need fewer rollbacks elsewhere. The choice also keeps held-while-waiting
zero under ROLLBACK. No universal winner is claimed.

Worker batches now meet at a bounded barrier in waves no larger than worker
capacity, before any resource lock. Actual measured overlaps name both threads
in the trace. Single-worker and one-batch paths do not use the barrier.
Sequential simulations sharing a tracer audit only their own event slice;
the caller retains aggregate history. Parser ordering and action-line error
diagnostics have regression tests. The unsupported policy winner table was
replaced with measured results.

## Remaining Final limitations

Multi-book handoff provenance/adjacency, early UNBLOCK ordering relative to
the contract, the normal CLI's NONE acceptance, and counter comparability
remain documented in [the audit](../docs/implementation_audit.md). The optional
blocking demo has synthetic statistics and does not bound barrier/join failures.
Free-threaded Python/PyPy correctness has not been established. Some older
stress tests do not prove completion or fairness on all inputs. Presentation
slides and a timed viva rehearsal are not supplied by this work.

The archive contains the actual README, inputs, tests, and documentation;
its build smoke checks include baseline runs, experiments, and the default
deadlock demo. Passing these checks is not a claim that every Final requirement
or known audit issue is resolved. See [Sam's guide](../docs/readme/samar_concurrency_deadlock.md)
for policies, synchronization, evidence, and limits.
