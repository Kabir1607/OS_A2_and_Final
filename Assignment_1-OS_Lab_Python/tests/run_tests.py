"""Python version of the C++ tests/run_tests.sh.

Runs the program on every tests/inputs/*.txt under FCFS and PRIORITY and
diffs the output against tests/expected/. Usage (from any directory):
    python3 tests/run_tests.py
"""

from __future__ import annotations

import difflib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    passed = failed = 0
    for input_path in sorted((ROOT / "tests" / "inputs").glob("*.txt")):
        for algorithm in ("FCFS", "PRIORITY"):
            expected_path = ROOT / "tests" / "expected" / f"{input_path.stem}_{algorithm}.out"
            proc = subprocess.run(
                [sys.executable, str(ROOT / "main.py"), str(input_path), algorithm],
                capture_output=True, text=True, check=False,
            )
            expected = expected_path.read_text()
            if proc.returncode == 0 and proc.stdout == expected:
                passed += 1
                continue
            failed += 1
            print(f"FAIL: {input_path.stem} {algorithm}")
            if proc.stderr:
                print(proc.stderr, end="")
            sys.stdout.writelines(difflib.unified_diff(
                expected.splitlines(keepends=True), proc.stdout.splitlines(keepends=True),
                fromfile=str(expected_path), tofile="actual",
            ))
    print(f"Passed: {passed}  Failed: {failed}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
