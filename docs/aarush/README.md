# Aarush A1–A5: memory management

[Read the PDF](memory_management.pdf) or edit [the LaTeX source](memory_management.tex).
The guide explains every public memory function, method, constructor, and
property through library operations, with seating diagrams, examples, errors,
statistics calculations, and test instructions.

Implementation: `src/library_sim/memory.py`.
Tests: `tests/contract/test_memory_contract.py`.
Task labels A1–A5 refer to Aarush's work items, not assignment numbers.

The code uses Python 3.10+ and the standard library. Run from the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.contract.test_memory_contract -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.contract.test_pyi_conformance -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -t . -v
```

The existing A1 regression and engine cross-check now use the Python A1
fixtures. The cross-check's seat capacity equals the sum of all readers'
requests, sufficient to prevent memory waiting without scanning a million slots.

To rebuild the PDF, install a LaTeX distribution with `pdflatex`, `fontenc`,
`geometry`, `amsmath`, `listings`, and `hyperref`. From the repository root:

```bash
aarush_latex_build=$(mktemp -d /tmp/aarush-latex.XXXXXX)
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$aarush_latex_build" docs/aarush/memory_management.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory="$aarush_latex_build" docs/aarush/memory_management.tex
cp "$aarush_latex_build/memory_management.pdf" docs/aarush/memory_management.pdf
```

Compilation intermediates stay in the temporary directory. No shell escape or
Python dependency installation is required.
