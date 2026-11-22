"""Contract tests for library_sim.parser (owner: Kabir). Also task K7:
one bad-input case per validation rule."""

from __future__ import annotations

import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

import tests  # noqa: F401
from library_sim.errors import InputError
from library_sim.models import ReaderSpec, ResourceSpec, SimulationInput
from library_sim.parser import parse_file, parse_reader_row, parse_text

SPEC_SAMPLE = """5
2
R1,0,3,7,REGULAR,2,0
R2,1,1,4,FACULTY,1,0
R3,2,3,5,REGULAR,3,0
R4,3,2,6,RESEARCHER,1,0
R5,4,1,3,FACULTY,2,0
"""


class ValidInput(unittest.TestCase):
    def test_spec_style_input(self) -> None:
        for mode in ("A2", "FINAL"):
            inp = parse_text(SPEC_SAMPLE, mode)
            self.assertIsInstance(inp, SimulationInput)
            self.assertEqual((inp.n, inp.quantum), (5, 2))
            self.assertEqual(inp.readers[0], ReaderSpec("R1", 0, 3, 7, "REGULAR", 2, 0))
            self.assertEqual((inp.resources, inp.actions, inp.has_resource_section),
                             ((), (), False))

    def test_file_order_kept_and_whitespace_tolerated(self) -> None:
        text = "2\r\n 3 \r\n R9 , 4 , 1 , 2 , FACULTY , 6 , 0 \r\nR10,0,2,1,REGULAR,1,0\r\n\r\n \n"
        inp = parse_text(text, "A2")
        self.assertEqual([r.id for r in inp.readers], ["R9", "R10"])
        self.assertEqual(inp.readers[0], ReaderSpec("R9", 4, 1, 2, "FACULTY", 6, 0))
        self.assertEqual(inp.quantum, 3)

    def test_byte_order_mark(self) -> None:
        self.assertEqual(parse_text("﻿1\n1\nR1,0,1,1,A,1,0\n", "A2").n, 1)

    def test_space_req_bounds_accepted(self) -> None:
        for k in (1, 6):
            self.assertEqual(parse_reader_row(f"R1,0,1,1,A,{k},0", 3).space_req, k)

    def test_parse_file(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "in.txt"
            path.write_text(SPEC_SAMPLE, encoding="utf-8")
            self.assertEqual(parse_file(str(path), "A2").n, 5)
            with self.assertRaises(InputError) as ctx:
                parse_file(str(Path(d) / "missing.txt"), "A2")
            self.assertIn("cannot open", str(ctx.exception))
            bad = Path(d) / "bad.txt"
            bad.write_bytes(b"\xff\xfe\x00")
            with self.assertRaises(InputError):
                parse_file(str(bad), "A2")

    def test_bad_mode(self) -> None:
        with self.assertRaises(ValueError):
            parse_text(SPEC_SAMPLE, "A1")  # type: ignore[arg-type]


class InvalidInput(unittest.TestCase):
    CASES = [
        # (description, text, message fragment, line_no)
        ("empty file", "", "empty", None),
        ("only blank lines", "\n \n", "empty", None),
        ("N zero", "0\n2\n", "N must be at least 1", 1),
        ("N not integer", "two\n2\n", "N must be an integer", 1),
        ("N with underscore", "1_0\n2\n", "N must be an integer", 1),
        ("Q missing", "1\n", "missing the quantum", 2),
        ("Q zero", "1\n0\nR1,0,1,1,A,1,0\n", "Q must be at least 1", 2),
        ("Q decimal", "1\n1.5\nR1,0,1,1,A,1,0\n", "Q must be an integer", 2),
        ("too few rows", "3\n2\nR1,0,1,1,A,1,0\nR2,0,1,1,A,1,0\n", "only 2 reader row(s)", 5),
        ("blank row inside", "2\n2\n\nR2,0,1,1,A,1,0\n", "expected 7 fields", 3),
        ("A1-style 5 fields", "1\n2\nR1,0,1,1,A\n", "expected 7 fields", 3),
        ("8 fields", "1\n2\nR1,0,1,1,A,1,0,9\n", "expected 7 fields", 3),
        ("empty ID", "1\n2\n,0,1,1,A,1,0\n", "ID must not be empty", 3),
        ("ID with space", "1\n2\nR 1,0,1,1,A,1,0\n", "must not contain whitespace", 3),
        ("duplicate ID", "2\n2\nR1,0,1,1,A,1,0\nR1,2,1,1,A,1,0\n", "duplicate reader ID R1", 4),
        ("negative arrival", "1\n2\nR1,-1,1,1,A,1,0\n", "ARRIVAL must be >= 0", 3),
        ("arrival not integer", "1\n2\nR1,x,1,1,A,1,0\n", "ARRIVAL must be an integer", 3),
        ("priority zero", "1\n2\nR1,0,0,1,A,1,0\n", "PRIORITY must be >= 1", 3),
        ("service zero", "1\n2\nR1,0,1,0,A,1,0\n", "SERVICE must be >= 1", 3),
        ("service decimal", "1\n2\nR1,0,1,2.5,A,1,0\n", "SERVICE must be an integer", 3),
        ("empty category", "1\n2\nR1,0,1,1, ,1,0\n", "CATEGORY must not be empty", 3),
        ("space_req zero", "1\n2\nR1,0,1,1,A,0,0\n", "SPACE_REQ must be between 1 and 6", 3),
        ("space_req seven", "1\n2\nR1,0,1,1,A,7,0\n", "SPACE_REQ must be between 1 and 6", 3),
        ("table_req one", "1\n2\nR1,0,1,1,A,1,1\n", "TABLE_REQ must be 0", 3),
        ("table_req blank", "1\n2\nR1,0,1,1,A,1,\n", "TABLE_REQ must be an integer", 3),
    ]

    def test_each_rule(self) -> None:
        for desc, text, fragment, line_no in self.CASES:
            for mode in ("A2", "FINAL"):
                with self.subTest(case=desc, mode=mode):
                    with self.assertRaises(InputError) as ctx:
                        parse_text(text, mode)
                    self.assertIn(fragment, str(ctx.exception))
                    self.assertEqual(ctx.exception.line_no, line_no)

    def test_a2_rejects_resource_sections(self) -> None:
        text = SPEC_SAMPLE + "1\nJOURNAL,1\n0\n"
        with self.assertRaises(InputError) as ctx:
            parse_text(text, "A2")
        self.assertEqual(ctx.exception.line_no, 8)
        self.assertIn("unexpected content", str(ctx.exception))


class FinalHandoff(unittest.TestCase):
    """[CONTRACT 6] + the hand-off to Samar's resource_parser."""

    def test_a2_and_resource_free_final_never_import_resource_parser(self) -> None:
        sys.modules.pop("library_sim.resource_parser", None)
        # A stand-in WITHOUT parse_resource_sections: if the parser touched it,
        # these calls would raise AttributeError.
        poison = types.ModuleType("library_sim.resource_parser")
        with mock.patch.dict(sys.modules, {"library_sim.resource_parser": poison}):
            self.assertEqual(parse_text(SPEC_SAMPLE, "A2").n, 5)
            self.assertFalse(parse_text(SPEC_SAMPLE + "\n\n", "FINAL").has_resource_section)

    def test_final_calls_parse_resource_sections(self) -> None:
        calls: list[tuple[object, ...]] = []
        resources = (ResourceSpec("JOURNAL", 1),)

        def fake_parse(lines, start, readers):  # type: ignore[no-untyped-def]
            calls.append((list(lines), start, readers))
            return resources, ()

        fake = types.ModuleType("library_sim.resource_parser")
        fake.parse_resource_sections = fake_parse  # type: ignore[attr-defined]
        text = SPEC_SAMPLE + "1\nJOURNAL,1\n0\n\n"
        with mock.patch.dict(sys.modules, {"library_sim.resource_parser": fake}):
            import library_sim
            with mock.patch.object(library_sim, "resource_parser", fake, create=True):
                inp = parse_text(text, "FINAL")

        self.assertEqual(len(calls), 1)
        lines, start, readers = calls[0]
        self.assertEqual(start, 7)                        # 0-based index of the R line
        self.assertEqual(lines[start], "1")               # type: ignore[index]
        self.assertEqual(lines[-1], "0")                  # trailing blanks already stripped
        self.assertEqual([r.id for r in readers], ["R1", "R2", "R3", "R4", "R5"])  # type: ignore[attr-defined]
        self.assertEqual(inp.resources, resources)
        self.assertTrue(inp.has_resource_section)

    def test_errors_from_resource_parser_propagate(self) -> None:
        def fake_parse(lines, start, readers):  # type: ignore[no-untyped-def]
            raise InputError("unknown resource LAPTOP", start + 2)

        fake = types.ModuleType("library_sim.resource_parser")
        fake.parse_resource_sections = fake_parse  # type: ignore[attr-defined]
        with mock.patch.dict(sys.modules, {"library_sim.resource_parser": fake}):
            import library_sim
            with mock.patch.object(library_sim, "resource_parser", fake, create=True):
                with self.assertRaises(InputError) as ctx:
                    parse_text(SPEC_SAMPLE + "1\nLAPTOP,1\n0\n", "FINAL")
        self.assertEqual(ctx.exception.line_no, 9)


if __name__ == "__main__":
    unittest.main()
