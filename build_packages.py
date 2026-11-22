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
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src" / "library_sim"
DIST = ROOT / "dist"
FINAL_ONLY = {
    "resource_parser.py", "trace.py", "resources.py", "workers.py", "deadlock.py",
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
    package.mkdir()
    for source in SRC.glob("*.py"):
        if mode == "A2" and source.name in FINAL_ONLY:
            continue
        shutil.copy2(source, package / source.name)
    (directory / "main.py").write_text(_main(mode), encoding="utf-8", newline="\n")
    (directory / "README.txt").write_text(
        f"Smart Library {mode} submission. Run: python3 main.py ...\n",
        encoding="utf-8",
    )


def _zip_stage(stage: Path, archive: Path) -> None:
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
        for path in stage.rglob("*"):
            if path.is_file():
                output.write(path, path.relative_to(stage))


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
            subprocess.run(
                ["python3", "-c", "import library_sim.cli"],
                cwd=smoke,
                check=True,
                env={"PYTHONPATH": str(smoke)},
            )
    print(f"built {DIST / 'a2.zip'} and {DIST / 'final.zip'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
