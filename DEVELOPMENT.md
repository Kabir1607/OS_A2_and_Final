# Developer guide (A2 + Final shared code)

- **Contract:** `library_sim.pyi`: every module's signatures and behaviour rules.
- **Tasks:** `division_of_work.txt`.
- **Python:** 3.10+. Standard library only at runtime.

## Layout

```
library_sim.pyi          interface contract (source of truth)
src/library_sim/         the shared package: one module per .pyi section
tests/contract/          one test_<module>_contract.py per module + test_pyi_conformance.py
tests/fakes/             shared fakes (fake_<module>.py), published by each owner
tests/integration/       cross-module tests; they skip until the modules they need exist
docs/readme/             README sections, assembled into the A2 and Final READMEs
Assignment_1-OS_Lab_Python/   the standalone A1 port (an A1 snapshot of the shared modules)
```

The package is under `src/` on purpose. A `library_sim/` folder next to
`library_sim.pyi` would be shadowed by the stub in IDEs and type
checkers.

## Run the tests

From the repository root:

```bash
python3 -m unittest discover -s tests -t . -v                 # everything
python3 -m unittest tests.contract.test_pyi_conformance -v    # does my module match the .pyi?
```

`test_pyi_conformance` reads `library_sim.pyi` and checks every module
that exists in `src/library_sim/` against its section:
- function and method parameter names, kinds and order
- dataclass fields and their order
- enum values
- properties and constants

Modules that don't exist yet are skipped. Run it before every PR.

To import the package from your own scripts: `sys.path.insert(0, "src")`,
or run with `PYTHONPATH=src`.

## Ready to use now (Kabir)

| Module | What you get |
|---|---|
| `errors` | `InputError(message, line_no)`: `str()` gives `line N: message`. `UsageError` |
| `models` | constants, `State` + `LEGAL_TRANSITIONS`, all enums, `ReaderSpec`, `ResourceSpec`, `Action`, `SimulationInput` (`.n`, `.reader()`, `.actions_for()`), `Reader` (`.transition()` asserts legality), `ReaderResult` |
| `scheduler` | `fcfs_key`, `priority_key`, `key_for`, heap-based `ReadyQueue` |
| `parser` | `parse_text(text, mode)`, `parse_file(path, mode)`, `parse_reader_row(line, line_no)`. In FINAL mode it calls `resource_parser.parse_resource_sections(lines, start, readers)` (Samar). `lines` has trailing blank lines removed, and `start` is the 0-based index of the `R` line |
| `metrics` | `compute_process_metrics(results)` (sorted by ID; asserts A ≤ M ≤ S ≤ C and no negative waiting), `compute_summary(metrics)` |
| `output` | `fmt_decimal`, `format_a1`, `format_a2`, `format_final`, `write_output`. PoolStats / ResourceStats / CheckStats are only read through their attributes, so the module needs none of the other modules at run time |
| `a1` | the A1 port. `run_a1(readers, scheduler)` is the reference for the K10 cross-check |

None of these need fakes, because the real modules are done. Use them directly.

## Waiting on other owners

- `tests/integration/test_engine_vs_a1.py` (K10) is active and passing:
  with a seat pool big enough that nobody waits for memory,
  `simulate(..., "A2")` gives the same START/COMPLETION as the A1 port on
  all 11 A1 inputs plus 200 random ones.
- `parser` in FINAL mode needs Samar's `resource_parser.py`.
