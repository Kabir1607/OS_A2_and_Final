"""Error types shared by every part of the simulator."""

from __future__ import annotations


class InputError(Exception):
    """Malformed or impossible input.

    The CLI catches it, prints ``Error: <message>`` to stderr and exits with
    status 1. ``line_no`` is the 1-based line in the input file, if known.
    """

    def __init__(self, message: str, line_no: int | None = None) -> None:
        self.message = message
        self.line_no = line_no
        super().__init__(str(self))

    def __str__(self) -> str:
        if self.line_no is None:
            return self.message
        return f"line {self.line_no}: {self.message}"


class UsageError(Exception):
    """Bad command-line arguments (wrong count, unknown scheduler/allocator)."""
