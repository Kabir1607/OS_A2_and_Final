<!-- Urvashi-owned README section: engine, CLI, testing, and packaging. -->

## Engine, CLI, and Packaging

The simulation engine is a discrete-event coordinator. It advances an integer
virtual clock to the next arrival or completion, drains all changes at that
timestamp, then samples seat occupancy. It never sleeps. Reader lifecycle
changes go through `Reader.transition()`, while memory allocation remains in
`memory.py`.

The event order is:

1. completions, in reader-ID order;
2. arrivals, in reader-ID order;
3. strict FIFO memory admission;
4. idle librarians are filled from the scheduler queue.

Final-mode resource modules are loaded lazily. Therefore an A2 package can
run without `resource_parser.py`, `trace.py`, `resources.py`, `workers.py`, or
`deadlock.py`. A resource-free Final run uses the same A2 loop and adds the
required zero-valued CHECK lines.

### Unit testing

From the repository root:

```bash
python3 -m unittest tests.contract.test_engine_fake_contract -v
python3 -m unittest tests.contract.test_pyi_conformance -v
python3 -m unittest discover -s tests -t . -v
```

The A1 cross-check becomes active automatically after `memory.py` is added:

```bash
python3 -m unittest tests.integration.test_engine_vs_a1 -v
```

To run the CLI after all collaborator modules are present:

```bash
PYTHONPATH=src python3 -c \
  'from library_sim.cli import a2_main; raise SystemExit(a2_main(["INPUT", "FCFS", "FIRST_FIT", "OUTPUT"]))'
```

Build both independent submissions with:

```bash
python3 build_packages.py
```

The archives are written to `dist/a2.zip` and `dist/final.zip`; the build
script extracts each archive into a clean directory and verifies package
imports.
