"""Focused contract checks for Urvashi's shared engine fake."""

from __future__ import annotations

import unittest

import tests  # noqa: F401
from library_sim.models import Allocator, ReaderSpec, Scheduler, SimulationInput
from tests.fakes.fake_engine import SimulationResultFake, simulate


class FakeEngineContract(unittest.TestCase):
    """Keep the fake useful to Aarush and Samar before integration."""

    def test_returns_stable_result_shape(self) -> None:
        inp = SimulationInput(
            quantum=1,
            readers=(
                ReaderSpec("R2", 3, 1, 2, "A"),
                ReaderSpec("R1", 0, 2, 1, "A"),
            ),
        )
        result = simulate(inp, Scheduler.FCFS, Allocator.FIRST_FIT, "A2")
        self.assertIsInstance(result, SimulationResultFake)
        self.assertEqual(result.readers[0].id, "R1")
        self.assertEqual(result.incomplete, ())
        self.assertEqual(result.pool.name, "SPACE")


if __name__ == "__main__":
    unittest.main()
