"""Build and smoke-test the independent A2 and Final zip submissions.

Usage:
    python3 build_packages.py

The script copies the shared package into temporary staging directories,
writes a mode-specific ``main.py``, removes Final-only modules from A2, and
executes each archive from a clean temporary directory.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
import zipfile
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "library_sim"
DIST = ROOT / "dist"
FINAL_ONLY = {
    "resource_parser.py", "trace.py", "resources.py", "workers.py", "deadlock.py",
}

# These tests/fakes deliberately import the Final subsystem. A2 ships its
# applicable tests and fixtures, not a suite that fails on absent Final files.
FINAL_TESTS = {
    "test_concurrency_stress.py", "test_deadlock_contract.py",
    "test_resource_parser_contract.py", "test_resources_contract.py",
    "test_trace_contract.py", "test_workers_contract.py",
    "test_samar_regressions.py", "test_policy_experiments_contract.py",
    "fake_resources.py", "fake_workers.py",
}


def _main(mode: str) -> str:
    """Return a tiny entrypoint that keeps package imports mode-specific."""
    function = "a2_main" if mode == "A2" else "final_main"
    return (
        "import sys\n"
        "from library_sim.cli import " + function + "\n"
        "raise SystemExit(" + function + "(sys.argv[1:]))\n"
    )


def _stage(mode: str, directory: Path) -> None:
    package = directory / "library_sim"
    package.mkdir(parents=True)
    for source in SRC.glob("*.py"):
        if mode == "A2" and source.name in FINAL_ONLY:
            continue
        shutil.copy2(source, package / source.name)
    (directory / "main.py").write_text(_main(mode), encoding="utf-8", newline="\n")
    source_folder = "Assignment_2-OS_Lab_Python" if mode == "A2" else "Final-OS_Lab_Python"
    readme = (ROOT / source_folder / "README.md").read_text(encoding="utf-8")
    # The canonical README lives one folder below the source repository root;
    # in the ZIP it is at the root, so its documentation links move accordingly.
    readme = readme.replace("../docs/", "docs/")
    (directory / "README.md").write_text(readme, encoding="utf-8")
    # Preserve canonical source-document links used by the supporting guides.
    for folder in ("Assignment_2-OS_Lab_Python", "Final-OS_Lab_Python"):
        (directory / folder).mkdir()
        shutil.copy2(ROOT / folder / "README.md", directory / folder / "README.md")
    shutil.copy2(ROOT / "library_sim.pyi", directory / "library_sim.pyi")
    for name in ("tests", "docs"):
        shutil.copytree(ROOT / name, directory / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(ROOT / "inputs" / "a2", directory / "inputs" / "a2")
    # The retained A1 regressions and cross-check read these Python fixtures.
    a1 = directory / "Assignment_1-OS_Lab_Python"
    shutil.copytree(ROOT / "Assignment_1-OS_Lab_Python", a1,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pdf"))
    if mode == "A2":
        for path in (directory / "tests").rglob("*.py"):
            if path.name in FINAL_TESTS:
                path.unlink()
    else:
        for path in (ROOT / "inputs").glob("*.txt"):
            shutil.copy2(path, directory / "inputs" / path.name)
        shutil.copytree(ROOT / "inputs" / "policy", directory / "inputs" / "policy")


def _zip_stage(stage: Path, archive: Path) -> None:
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in stage.rglob("*"):
            if path.is_file():
                output.write(path, path.relative_to(stage))


SMOKE_INPUT = "2\n2\nR1,0,1,3,REGULAR,4,0\nR2,1,2,2,REGULAR,3,0\n"


def _smoke_run(smoke: Path, mode: str) -> None:
    """Run real commands from an extracted archive with no source-path help."""
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    def run(arguments: list[str]) -> None:
        subprocess.run(["python3", *arguments], cwd=smoke, env=env,
                       check=True, timeout=30, capture_output=True, text=True)

    (smoke / "smoke_input.txt").write_text(SMOKE_INPUT, encoding="utf-8")
    for scheduler in ("FCFS", "PRIORITY"):
        for allocator in ("FIRST_FIT", "BEST_FIT", "WORST_FIT"):
            run(["main.py", "smoke_input.txt", scheduler, allocator, "smoke_output.txt"])
            output = (smoke / "smoke_output.txt").read_text(encoding="utf-8")
            if ("POOL,SPACE,6,4,60.0000,0\n" not in output
                    or ("CHECK," in output) != (mode == "FINAL")):
                raise SystemExit(f"{mode} smoke run produced unexpected output:\n{output}")
    run(["-m", "unittest", "discover", "-s", "tests", "-t", ".", "-q"])
    run(["-m", "library_sim.experiments", "allocators", "inputs/a2/comparison.txt",
         "--md", "allocator-report.md"])
    if mode == "FINAL":
        run(["main.py", "--demo-deadlock"])
        run(["-m", "library_sim.experiments", "policies", "inputs/spec_sample.txt",
             "--repeats", "2", "--md", "policy-report.md"])
    print(f"{mode}: extracted tests, six CLI combinations, and experiments passed")


def main() -> int:
    """Build both archives and verify that each can import its entrypoint."""
    required = {"engine.py", "cli.py", "memory.py"}
    missing = sorted(name for name in required if not (SRC / name).exists())
    if missing:
        raise SystemExit(
            "Cannot build submissions; missing collaborator modules: "
            + ", ".join(missing)
        )
    DIST.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="library-sim-build-") as root:
        root_path = Path(root)
        for mode in ("A2", "FINAL"):
            stage = root_path / mode
            _stage(mode, stage)
            archive = DIST / f"{mode.lower()}.zip"
            _zip_stage(stage, archive)
            smoke = root_path / f"{mode}-smoke"
            smoke.mkdir()
            with zipfile.ZipFile(archive) as source:
                source.extractall(smoke)
            _smoke_run(smoke, mode)
    print(f"built {DIST / 'a2.zip'} and {DIST / 'final.zip'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
