# Aarush: memory, fixtures, experiments, and A2 delivery

[Read the PDF](memory_management.pdf) or edit [the LaTeX source](memory_management.tex).
The guide explains memory and experiment functions through library operations,
with inputs/results/errors, seating examples, metrics, and verification.
The [complete A2 README](../../Assignment_2-OS_Lab_Python/README.md) is the
submission document; this directory contains supporting teaching/evidence material.

Aarush A1–A7 (including A7b/A7c), A9, and A10 are implemented. A8 runtime
visualization remains optional and absent. These are team task IDs, not assignment
numbers. Source is in `src/library_sim`; the public contract is unchanged.

| Work | Evidence |
|---|---|
| A1–A5 | Real memory module; 25 original checks including real engine integration |
| A6 | Eight edge cases + comparison input, 54 golden exports; [manual anchors](fixture_checks.md), [independent workbook](fixture_derivations.md) |
| A7 | [Six-way allocator results](allocator_comparison.md) and Python A1 baseline discussion |
| A7b | Complete experiments API/CLI; [720 policy-run spreads/rankings](policy_comparison.md), [JSON](policy_results.json) |
| A7c | Independent slot-list fake; 24 shared behavior tests also run against it |
| A9–A10 | Allocation discussion, complete A2 README, archive inclusion and clean-directory checks |
| Sam fixes | [Actual overlap](overlap_evidence.txt); parser/order and shared-tracer regressions; [audit history/current status](../implementation_audit.md) |

Python 3.10+ and standard library only. Snapshot on Python 3.12.3: 173 root
tests (172 pass, one expected skip), standalone A1 17 passes plus 20/20 golden
cases. Timings and thread winners may vary on other runs/interpreters.

From the source repository root:

```bash
python3 -m unittest discover -s tests -t . -v
python3 -m unittest tests.contract.test_pyi_conformance -v
python3 -m unittest tests.integration.test_a2_fixtures -v
PYTHONPATH=src python3 -m library_sim.experiments allocators inputs/a2/comparison.txt --md allocator-report.md
PYTHONPATH=src python3 -m library_sim.experiments policies inputs/policy/*.txt --repeats 30 --md policy-report.md
python3 build_packages.py
```

Golden regeneration is explicit: `python3 -m tests.reference_a2 --write`.
Review manual anchors and derivations before accepting updated expected values;
never use production output as its own expected result. P6 is reproducible via
`python3 inputs/policy/generate_stress.py`, seed 3710. Final measurements include
in-memory ownership tracing and bounded worker barrier coordination.

To rebuild the PDF, use pdflatex with fontenc, geometry, amsmath, listings and
hyperref. From the source repository root:

```bash
aarush_latex_build=$(mktemp -d /tmp/aarush-latex.XXXXXX)
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$aarush_latex_build" docs/aarush/memory_management.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$aarush_latex_build" docs/aarush/memory_management.tex
cp "$aarush_latex_build/memory_management.pdf" docs/aarush/memory_management.pdf
```

Compile again if references request it. Intermediates stay outside the repo.
Archives include this guide, examples, real READMEs and applicable tests. Known
remaining Final issues and presentation work are documented in the audit;
completing these Aarush tasks is not a claim of complete Final compliance.
