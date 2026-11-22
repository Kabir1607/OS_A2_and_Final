# Smart Library: CS-3710 OS Lab (A1 + A2 + Final Project)

The group's working repository. Start here: this page explains what the
code base does today, where everything is, the rules you have to follow,
and how to start contributing.

> **Quick links**
> - [`library_sim.pyi`](library_sim.pyi): the interface contract. Every signature and every rule between modules.
> - [`division_of_work.txt`](division_of_work.txt): who does what (task IDs K*, U*, A*, S*, G*) and the integration gates.
> - [`context.md`](context.md): a summary of all three specs, plus the **TA-approved assumptions**.
> - [`DEVELOPMENT.md`](DEVELOPMENT.md): the developer guide (layout, running tests, what's usable now).
> - [`kabir_work_usage.txt`](kabir_work_usage.txt): how to use the finished foundation modules, with notes for each person.

---

## 1. What we're building

One simulator for the **Smart Library** scenario, built in three stages:

| Stage | Question it answers | Library mapping |
|---|---|---|
| **A1: Process management** | *Who is served next?* | Readers are processes, and 2 librarians serve them. **FCFS** and **non-preemptive PRIORITY** |
| **A2: Memory management** | *Where can the reader sit?* | 6 contiguous reading-seat slots. First/Best/Worst Fit, strict FIFO admission with head-of-line blocking |
| **Final: Concurrency** | *How do readers safely share books?* | 17 named books/journals, each with capacity 1. **Real threads**, locks, a deadlock demo and **deadlock prevention** (ROLLBACK and ORDERED) |

- **Two submissions:** A2 and the Final Project are separate `.zip`
  archives, and each must run on its own.
- **Presentation:** one joint presentation and viva covers both.
- **Grading:** a private automated test suite checks our input/output
  formats exactly, so the formats in the specs are mandatory.
- **Why Python:** A1 was written in C++. A2 and the Final are in Python,
  and A1 has been ported so the A1 behaviour is kept exactly.

## 2. Status: what works today

| Module (`src/library_sim/`) | Owner | Status |
|---|---|---|
| `errors.py`, `models.py`, `scheduler.py` | Kabir | ✅ done |
| `a1.py` (A1 port, byte-identical to the C++ output) | Kabir | ✅ done |
| `parser.py` (A2/Final process section + validation) | Kabir | ✅ done (Final-mode hand-off waits for `resource_parser.py`) |
| `metrics.py`, `output.py` (A1, A2 and Final formats) | Kabir | ✅ done |
| `memory.py` (seats, allocators, FIFO admission, occupancy) | Aarush | ✅ done |
| `experiments.py` (allocator + policy comparisons) | Aarush | ⬜ not started |
| `engine.py` (A2 loop + resource-free Final) | Urvashi | ✅ done; the Final loop with resources is written but waits for Samar's modules |
| `cli.py` (`a2_main`, `final_main`, `--demo-deadlock`) | Urvashi | ✅ A2 and resource-free Final work; `--policy`, `--trace`, `--demo-deadlock` and inputs with resources wait for Samar's modules |
| `build_packages.py` (the two zips) | Urvashi | ✅ builds `dist/a2.zip` + `dist/final.zip` and runs each from a clean folder |
| `resource_parser.py`, `trace.py`, `resources.py`, `workers.py`, `deadlock.py` | Samar | ⬜ not started |

**Tests today:** 76 tests pass on Python 3.10 and 3.14, none skipped. They
include the engine-vs-A1 cross-check (K10: 211 inputs x 2 schedulers) and
the "resource-free Final = A2" check. `mypy --strict` only reports the
missing modules from Samar.

**What you can run today:**

```bash
# A1 (standalone Python port)
cd Assignment_1-OS_Lab_Python
python3 main.py input.txt FCFS          # or PRIORITY
python3 tests/run_tests.py              # A1 regression: 20/20 vs the C++ expected outputs
cd ..

# A2 and Final, from the repo root (the zips get their own main.py)
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import a2_main; raise SystemExit(a2_main(sys.argv[1:]))' INPUT FCFS FIRST_FIT OUTPUT
PYTHONPATH=src python3 -c 'import sys; from library_sim.cli import final_main; raise SystemExit(final_main(sys.argv[1:]))' INPUT FCFS FIRST_FIT OUTPUT --stats

# Build both submissions into dist/ (git-ignored) and smoke-test them
python3 build_packages.py
```

Final runs on inputs **with** resources, `--policy`, `--trace` and
`--demo-deadlock` stop with a clean `Error:` message until Samar's modules exist.

## 3. Where everything is

```
README.md                    ← you are here
library_sim.pyi              interface contract: signatures, data types, [CONTRACT 1-6] rules
division_of_work.txt         tasks per person + integration gates
context.md                   summary of the specs + TA-approved assumptions + open questions
DEVELOPMENT.md               developer guide
kabir_work_usage.txt         how to use the foundation modules

src/library_sim/             THE SHARED PACKAGE: all A2/Final code goes here
tests/contract/              one test_<module>_contract.py per module
tests/contract/test_pyi_conformance.py   checks every module against library_sim.pyi
tests/integration/           cross-module tests (skip until their modules exist)
tests/fakes/                 shared fakes: fake_<module>.py (see tests/fakes/README.md)
docs/readme/                 README sections; the A2 and Final READMEs are assembled from these

Assignment_1-OS_Lab_C++/     the original A1 (C++), with its test inputs/expected outputs and README
Assignment_1-OS_Lab_Python/  the standalone A1 Python port (its shared modules are copies of src/library_sim/)
Assignment_2-OS_Lab_Python/  the A2 specification PDF
Final-OS_Lab_Python/         the Final Project specification PDF
```

**The specifications:**

| Document | Location |
|---|---|
| A1 spec | `Assignment_1-OS_Lab_Python/OSLab_CS_3710__A1_Specifications.pdf` |
| A2 spec | `Assignment_2-OS_Lab_Python/OSLab_CS_3710__A2_Specifications.pdf` |
| Final spec | `Final-OS_Lab_Python/OSLab_CS_3710__Final_Project_Specifications.pdf` |
| Summary + TA-approved decisions | `context.md` (sections 2–6) |

## 4. Getting started

**Requirements:** Python 3.10 or newer. Standard library only, so there is
nothing to install.

```bash
# from the repository root
python3 -m unittest discover -s tests -t . -v               # all tests
python3 -m unittest tests.contract.test_pyi_conformance -v  # does the code match the contract?
PYTHONPATH=src python3 -c "from library_sim.parser import parse_text; print(parse_text('1\n2\nR1,0,1,3,REGULAR,2,0\n', 'A2'))"
```

**Why `src/`:** a `library_sim/` folder next to `library_sim.pyi` would be
shadowed by the stub in VS Code / Pylance / mypy, and every import would
show as broken. Inside the package, use relative imports
(`from .models import ReaderSpec`).

## 5. How to start contributing

1. **Find your tasks** in `division_of_work.txt`, under your name. Each
   has an ID: Kabir K*, Urvashi U*, Aarush A*, Samar S*, group G*.
2. **Read your section of `library_sim.pyi`.** Search for
   `library_sim/<your_module>.py`. Also read every `[CONTRACT n]` rule that
   names your module; the list is in the `.pyi` header. The `.pyi` is the
   source of truth: **don't rename, reorder or retype anything without
   asking the group first**.
3. **Read the spec sections behind your tasks** (PDF + `context.md`). Pay
   particular attention to the **TA-approved assumptions** at the end of
   `context.md`. The hidden tests will follow them.
4. **Publish early: a fake + contract tests, before your real code.**
   Others are blocked on you until you do.
   - `tests/fakes/fake_<module>.py`: same signatures and same behaviour
     rules as the `.pyi`.
   - `tests/contract/test_<module>_contract.py`: tests of those rules.
     Both your fake and your real module must pass them.
5. **Use what's already done** (see `kabir_work_usage.txt`):
   - `models` (all shared types)
   - `scheduler.ReadyQueue`
   - `parser.parse_file`
   - `metrics.compute_process_metrics` / `compute_summary`
   - `output.format_a2` / `format_final` / `write_output`

   For modules that aren't ready yet, use their owner's published fake.
   **Never write a private fake.**
6. **Implement** in `src/library_sim/<module>.py`.
7. **Before sharing or merging changes**, run the whole suite and the
   conformance test. Both must pass. Then get the review from task G2:
   - Kabir ↔ Urvashi
   - Aarush → Urvashi
   - Samar → Urvashi
   - Urvashi → Samar
8. **Write your README section** in `docs/readme/<your_name>_*.md`. Add your
   assumptions and limitations to
   `docs/readme/assumptions_limitations_optional.md` (the TODOs marked for you).

## 6. Rules every contribution must follow

### Graded input/output (exact: a private test suite checks it)
- **Input:** `N`, `Q`, then N rows of
  `ID,ARRIVAL,PRIORITY,SERVICE,CATEGORY,SPACE_REQ,TABLE_REQ`. Final inputs
  may continue with `R` resource rows and `K` action rows (Final spec §8).
  Parsing is done in `parser.py`.
- **Output:** no header row, no prose or debug text, UTF-8 with `\n`
  line endings. PROCESS lines sorted by ID, then SUMMARY, then POOL. The
  Final adds RESOURCE and CHECK lines. The exact formats are in
  `output.py`: build output only through `format_a2` / `format_final`.
- **Decimals:** 4 decimal places for every decimal statistic. Never 2.
- **Errors:** bad input or arguments print `Error: line N: ...` on stderr,
  exit with status 1 and write no output file. Never a traceback, never a hang.

### Simulation semantics
- Integer virtual time, event-driven, no real-time sleeping.
- The same input and options must give the same output. The only
  exception is the order of racing thread events in Final runs with
  contention.
- **Event order within one timestamp** (TA-approved, `context.md` §6.2 and
  the `Simulation` docstring in the `.pyi`):
  1. resource actions
  2. completions
  3. arrivals
  4. FIFO admission
  5. woken readers become READY
  6. librarians are filled
  7. actions due right after dispatch

  Repeat until nothing changes.
- **Resource-free baseline:** the Final run on a resource-free input must
  reproduce A2 **exactly**.

### Concurrency (Final)
- Only the engine's coordinator thread touches `Reader`, `ReadyQueue`,
  `SeatPool` and `AdmissionQueue`.
- Worker threads touch shared state **only** through `ResourceManager` and
  `Tracer`, which are internally locked. Every check and its update
  happen in **one** critical section.
- **No `sleep()` for correctness, no busy-waiting, no reliance on the GIL**
  for atomicity.
- Deadlock prevention is **on by default** (`DEFAULT_POLICY`). The unsafe
  demo must always be bounded.

### Packaging
- The A2 zip must run **without** the Final-only modules: `resource_parser`,
  `trace`, `resources`, `workers` and `deadlock` [CONTRACT 6]. Import those
  only inside Final-mode code.
- Each zip must run from a clean folder with a plain `python3`.

### Code
- Python 3.10+, standard library only at run time. Type hints on public
  functions.
- One module per responsibility. Keep scheduling, memory, synchronization
  and reporting separate (Final spec §11).
- Everyone must be able to explain **the whole system** in the viva, not
  just their own part. Read the others' modules too.

## 7. How the pieces come together (integration gates)

Independent work only gets each module as far as Gate 1. After that the
steps are sequential and need everyone. Urvashi leads; details in
`division_of_work.txt`.

| Gate | What happens | Who |
|---|---|---|
| 0 | Contracts frozen. Foundation merged ✅. Every owner's fakes and contract tests published | everyone |
| 1 | Each real module passes its own contract tests (the same ones as its fake) | each owner |
| 2 | **A2 integration:** engine + memory + foundation. K10 cross-check, A6 expected outputs, determinism → A2 comparison, A2 README, **A2 zip** | Urvashi, Aarush, Kabir |
| 3 | **Final integration:** engine + resources + workers, both policies, overlap evidence, deadlock demo | Urvashi, Samar |
| 4 | Policy comparison (ROLLBACK vs ORDERED) → choose `DEFAULT_POLICY` | Aarush, Samar |
| 5 | README results, trade-offs, assumptions, demo script, **Final zip**, checklist, viva dry run | everyone |

Gate 2 (the A2 zip) must never wait for Gate 3.

## 8. Questions and changes

- **A rule is unclear, or a signature needs to change:** raise it with
  the group. Update `library_sim.pyi` first, then the code.
- **A test fails at integration:** it goes to the owner of the module whose
  `[CONTRACT n]` rule was broken. If the rule itself was unclear, fix the
  `.pyi` first.
- **The spec is ambiguous:** check `context.md` §6 (open questions and
  TA-approved answers) before deciding, and record the decision in
  `docs/readme/assumptions_limitations_optional.md`.
- **Foundation modules** (errors, models, scheduler, parser, metrics,
  output, a1): ask Kabir.
