"""Contract and unit tests for library_sim.resource_parser (owner: Samar)."""

from __future__ import annotations

import unittest

import tests  # noqa: F401
from library_sim.errors import InputError
from library_sim.models import Action, ActionType, ReaderSpec, ResourceSpec
from library_sim.resource_parser import parse_resource_sections, validate_actions


class ResourceParserContract(unittest.TestCase):
    def setUp(self) -> None:
        self.readers = (
            ReaderSpec("R1", 0, 1, 6, "REGULAR", 1, 0),
            ReaderSpec("R2", 0, 2, 4, "FACULTY", 1, 0),
        )

    def test_valid_parsing(self) -> None:
        lines = [
            "2",
            "REFERENCE_BOOK,1",
            "JOURNAL,1",
            "4",
            "R1,0,ACQUIRE,REFERENCE_BOOK,1",
            "R1,5,RELEASE,REFERENCE_BOOK,1",
            "R2,1,ACQUIRE,JOURNAL,1",
            "R2,3,RELEASE,JOURNAL,1",
        ]
        resources, actions = parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(len(resources), 2)
        self.assertEqual(resources[0], ResourceSpec("REFERENCE_BOOK", 1))
        self.assertEqual(resources[1], ResourceSpec("JOURNAL", 1))
        self.assertEqual(len(actions), 4)
        self.assertEqual(actions[0].reader_id, "R1")
        self.assertEqual(actions[0].work_offset, 0)
        self.assertEqual(actions[0].action, ActionType.ACQUIRE)
        self.assertEqual(actions[0].resource_id, "REFERENCE_BOOK")
        self.assertEqual(actions[0].row_index, 0)

    def test_zero_resources_zero_actions(self) -> None:
        lines = ["0", "0"]
        resources, actions = parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(resources, ())
        self.assertEqual(actions, ())

    def test_missing_r(self) -> None:
        lines: list[str] = []
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 1)

    def test_non_integer_r(self) -> None:
        lines = ["two", "0"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 1)

    def test_too_few_resource_rows(self) -> None:
        lines = ["2", "REFERENCE_BOOK,1"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 3)

    def test_unknown_resource_name(self) -> None:
        lines = ["1", "UNKNOWN_ITEM,1", "0"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 2)
        self.assertIn("STANDARD_RESOURCES", str(ctx.exception))

    def test_capacity_not_one(self) -> None:
        lines = ["1", "JOURNAL,2", "0"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 2)
        self.assertIn("CAPACITY must be 1", str(ctx.exception))

    def test_duplicate_resource_declaration(self) -> None:
        lines = ["2", "JOURNAL,1", "JOURNAL,1", "0"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 3)

    def test_missing_k(self) -> None:
        lines = ["1", "JOURNAL,1"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 3)

    def test_too_few_action_rows(self) -> None:
        lines = ["1", "JOURNAL,1", "2", "R1,0,ACQUIRE,JOURNAL,1"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 5)

    def test_unknown_reader_in_action(self) -> None:
        lines = ["1", "JOURNAL,1", "1", "R99,0,ACQUIRE,JOURNAL,1"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 4)

    def test_undeclared_resource_in_action(self) -> None:
        lines = ["1", "JOURNAL,1", "1", "R1,0,ACQUIRE,REFERENCE_BOOK,1"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 4)

    def test_work_offset_exceeds_service(self) -> None:
        # R2 service is 4
        lines = ["1", "JOURNAL,1", "1", "R2,5,ACQUIRE,JOURNAL,1"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 4)

    def test_units_not_one(self) -> None:
        lines = ["1", "JOURNAL,1", "1", "R1,0,ACQUIRE,JOURNAL,2"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 4)

    def test_bad_action_verb(self) -> None:
        lines = ["1", "JOURNAL,1", "1", "R1,0,BORROW,JOURNAL,1"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 4)

    def test_extra_lines_after_k(self) -> None:
        lines = ["1", "JOURNAL,1", "1", "R1,0,ACQUIRE,JOURNAL,1", "EXTRA"]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertEqual(ctx.exception.line_no, 5)

    def test_double_acquire_validation(self) -> None:
        lines = [
            "1",
            "JOURNAL,1",
            "2",
            "R1,0,ACQUIRE,JOURNAL,1",
            "R1,1,ACQUIRE,JOURNAL,1",
        ]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertIn("double-acquired", str(ctx.exception))

    def test_release_without_hold_validation(self) -> None:
        lines = [
            "1",
            "JOURNAL,1",
            "1",
            "R1,0,RELEASE,JOURNAL,1",
        ]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertIn("unheld", str(ctx.exception))

    def test_unreleased_resource_at_completion(self) -> None:
        lines = [
            "1",
            "JOURNAL,1",
            "1",
            "R1,0,ACQUIRE,JOURNAL,1",
        ]
        with self.assertRaises(InputError) as ctx:
            parse_resource_sections(lines, 0, self.readers)
        self.assertIn("still holds", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
