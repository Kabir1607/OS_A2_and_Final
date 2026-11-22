# Aarush A1–A5: memory management

[Read the PDF](memory_management.pdf) or edit [the LaTeX source](memory_management.tex).
The guide explains every public memory function, method, constructor, and
property through library operations, with seating diagrams, examples, errors,
statistics calculations, and test instructions.

Checked against code revision `f69cd13` on 22 November 2026. See the
[implementation audit](../implementation_audit.md) for reviewed modules,
verified results, and remaining issues. This guide describes A1–A5 memory
work; it is not the complete A2 submission README.

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

At this revision, all 25 memory checks pass. Root discovery reports 133 passes
and one skip out of 134 tests. Standalone Python A1 passes 17 tests and its
golden-output runner passes 20 cases. These are Python 3.12.3 audit results,
not a guarantee for every future revision or interpreter.

| Work item | Current status |
|---|---|
| A1–A5 | Memory functions/classes and tests implemented. |
| A6 | Separate A2 inputs and hand-verified expected outputs remain to be added. |
| A7/A7b | `experiments.py` and measured allocator/full policy comparisons are absent. |
| A7c | Memory contract tests exist; the separate memory fake does not. |
| A8 | Guide diagrams exist; a runtime memory-map/timeline feature does not. |
| A9–A10 | Explanations exist here; a complete comparison-backed A2 README and archive remain unfinished. |

Sam's resource modules and Urvashi's ZIP builder now exist. Both archives run
from clean directories, but contain only Python modules, an entrypoint, and
a placeholder README. The builder does not include this guide, samples, or
tests. Final overlap/correctness limitations are recorded in the audit and
are separate from the passing memory checks.

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
