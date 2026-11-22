"""Contract tests for library_sim.models and library_sim.errors (owner: Kabir)."""

from __future__ import annotations

import dataclasses
import unittest

import tests  # noqa: F401  (puts src/ on sys.path)
from library_sim.errors import InputError, UsageError
from library_sim.models import (
    LEGAL_TRANSITIONS, NUM_LIBRARIANS, SEAT_CAPACITY, STANDARD_RESOURCES,
    Action, ActionType, Allocator, Reader, ReaderResult, ReaderSpec,
    ResourceSpec, Scheduler, SimulationInput, State,
)


class Constants(unittest.TestCase):
    def test_values(self) -> None:
        self.assertEqual(NUM_LIBRARIANS, 2)
        self.assertEqual(SEAT_CAPACITY, 6)

    def test_standard_resources(self) -> None:
        expected = ({f"OS_BOOK_{i}" for i in range(1, 11)}
                    | {"FICTION_1", "FICTION_2", "FICTION_3", "MAG_1", "MAG_2",
                       "REFERENCE_BOOK", "JOURNAL"})
        self.assertEqual(STANDARD_RESOURCES, frozenset(expected))
        self.assertIsInstance(STANDARD_RESOURCES, frozenset)

    def test_enums_parse_cli_strings(self) -> None:
        self.assertIs(Scheduler("FCFS"), Scheduler.FCFS)
        self.assertIs(Allocator("WORST_FIT"), Allocator.WORST_FIT)
        self.assertIs(ActionType("RELEASE"), ActionType.RELEASE)
        with self.assertRaises(ValueError):
            Scheduler("fcfs")                      # names are case-sensitive
        self.assertEqual(Scheduler.PRIORITY.value, "PRIORITY")


class Lifecycle(unittest.TestCase):
    def test_exact_transition_table(self) -> None:
        expected = {
            State.NEW: {State.BLOCKED_MEMORY, State.READY},
            State.BLOCKED_MEMORY: {State.READY},
            State.READY: {State.RUNNING},
            State.RUNNING: {State.BLOCKED_RESOURCE, State.TERMINATED},
            State.BLOCKED_RESOURCE: {State.READY},
            State.TERMINATED: set(),
        }
        self.assertEqual({k: set(v) for k, v in LEGAL_TRANSITIONS.items()}, expected)
        with self.assertRaises(TypeError):
            LEGAL_TRANSITIONS[State.NEW] = frozenset()  # type: ignore[index]

    def test_reader_transition(self) -> None:
        r = Reader(ReaderSpec("R1", 0, 1, 2, "REGULAR"))
        self.assertIs(r.state, State.NEW)
        self.assertEqual(r.id, "R1")
        path = [State.BLOCKED_MEMORY, State.READY, State.RUNNING, State.BLOCKED_RESOURCE,
                State.READY, State.RUNNING, State.TERMINATED]
        for state in path:
            r.transition(state)
        self.assertIs(r.state, State.TERMINATED)
        for bad_from, bad_to in [(State.NEW, State.RUNNING), (State.READY, State.TERMINATED),
                                 (State.BLOCKED_RESOURCE, State.RUNNING)]:
            reader = Reader(ReaderSpec("R2", 0, 1, 1, "A"), state=bad_from)
            with self.assertRaises(AssertionError):
                reader.transition(bad_to)
            self.assertIs(reader.state, bad_from)  # unchanged after a failed transition

    def test_reader_defaults(self) -> None:
        r = Reader(ReaderSpec("R1", 0, 1, 2, "A"))
        self.assertEqual((r.actions, r.executed, r.next_action, r.resource_wait), ((), 0, 0, 0))
        self.assertIsNone(r.mem_admit)
        self.assertIsNone(r.start)
        self.assertIsNone(r.completion)


class Records(unittest.TestCase):
    def test_reader_spec(self) -> None:
        spec = ReaderSpec("R1", 0, 3, 7, "REGULAR")
        self.assertEqual((spec.space_req, spec.table_req), (1, 0))
        with self.assertRaises(dataclasses.FrozenInstanceError):
            spec.arrival = 5  # type: ignore[misc]
        self.assertEqual(hash(spec), hash(ReaderSpec("R1", 0, 3, 7, "REGULAR")))

    def test_reader_result_default_resource_wait(self) -> None:
        self.assertEqual(ReaderResult("R1", 0, 1, 2, 0, 2, 0).resource_wait, 0)

    def test_simulation_input(self) -> None:
        a = [Action("R1", 3, ActionType.RELEASE, "JOURNAL", 1, 1),
             Action("R2", 0, ActionType.ACQUIRE, "MAG_1", 1, 2),
             Action("R1", 0, ActionType.ACQUIRE, "JOURNAL", 1, 0),
             Action("R1", 3, ActionType.ACQUIRE, "MAG_2", 1, 3)]
        inp = SimulationInput(
            quantum=2,
            readers=(ReaderSpec("R2", 1, 1, 4, "A"), ReaderSpec("R1", 0, 1, 4, "A")),
            resources=(ResourceSpec("JOURNAL", 1),),
            actions=tuple(a),
            has_resource_section=True,
        )
        self.assertEqual(inp.n, 2)
        self.assertEqual(inp.reader("R1").arrival, 0)
        with self.assertRaises(KeyError):
            inp.reader("R9")
        # Sorted by offset, ties broken by row order (not by action type).
        self.assertEqual([x.row_index for x in inp.actions_for("R1")], [0, 1, 3])
        self.assertEqual(inp.actions_for("R3"), ())

    def test_simulation_input_without_resources(self) -> None:
        inp = SimulationInput(quantum=1, readers=(ReaderSpec("R1", 0, 1, 1, "A"),))
        self.assertEqual((inp.resources, inp.actions, inp.has_resource_section), ((), (), False))


class Errors(unittest.TestCase):
    def test_input_error(self) -> None:
        e = InputError("bad value", 4)
        self.assertEqual((e.message, e.line_no, str(e)), ("bad value", 4, "line 4: bad value"))
        self.assertEqual(str(InputError("empty")), "empty")
        self.assertIsNone(InputError("x").line_no)
        self.assertTrue(issubclass(UsageError, Exception))


if __name__ == "__main__":
    unittest.main()
