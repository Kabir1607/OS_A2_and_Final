"""Test suite. Run from the repository root:

    python3 -m unittest discover -s tests -t . -v

Importing this package puts src/ on sys.path, so `import library_sim` works.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
