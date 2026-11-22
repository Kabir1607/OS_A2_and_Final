"""Contract tests for library_sim.metrics (owner: Kabir)."""

from __future__ import annotations

import unittest

import tests  # noqa: F401
from library_sim.metrics import ProcessMetrics, compute_process_metrics, compute_summary
from library_sim.models import ReaderResult


def rr(pid: str, a: int, b: int, s: int, c: int, m: int | None = None,
       rw: int = 0, prio: int = 1) -> ReaderResult:
    return ReaderResult(pid, a, prio, b, s, c, a if m is None else m, rw)


class PerReader(unittest.TestCase):
    def test_formulas_and_identity(self) -> None:
        # A=2, M=4, S=6, C=15, B=5, ResourceWait=3 -> TotalWait = 15-2-5 = 8 = 2 + 3 + 3
        m = compute_process_metrics([rr("R1", 2, 5, 6, 15, m=4, rw=3)])[0]
        self.assertEqual(m, ProcessMetrics("R1", 2, 1, 5, 6, 15, 8, 13, 4, 4, 2, 3, 3))
        self.assertEqual(m.waiting, m.mem_wait + m.ready_wait + m.resource_wait)

    def test_a2_reduces_to_a1(self) -> None:
        m = compute_process_metrics([rr("R1", 0, 3, 4, 7)])[0]
        self.assertEqual((m.mem_wait, m.resource_wait, m.ready_wait), (0, 0, m.waiting))

    def test_sorted_by_string_id(self) -> None:
        ms = compute_process_metrics([rr("R2", 0, 1, 0, 1), rr("R10", 0, 1, 0, 1),
                                      rr("R1", 0, 1, 1, 2)])
        self.assertEqual([m.id for m in ms], ["R1", "R10", "R2"])

    def test_rejects_inconsistent_timestamps(self) -> None:
        bad = [
            rr("R1", 5, 1, 4, 6),              # S < A
            rr("R1", 0, 1, 2, 3, m=3),          # S < M
            rr("R1", 0, 5, 0, 3),               # C - A < B (negative waiting)
            rr("R1", 0, 1, 0, 2, rw=5),         # resource wait larger than total wait
        ]
        for r in bad:
            with self.subTest(result=r), self.assertRaises(AssertionError):
                compute_process_metrics([r])


class Summary(unittest.TestCase):
    def test_hand_computed(self) -> None:
        # E = max C - min A = 13 - 1 = 12; sum B = 4 + 6 + 3 = 13
        ms = compute_process_metrics([
            rr("R1", 1, 4, 1, 5),
            rr("R2", 2, 6, 7, 13, m=7),        # memory wait 5, blocked for memory
            rr("R3", 3, 3, 5, 10, m=4, rw=1),  # memory wait 1
        ])
        s = compute_summary(ms)
        self.assertAlmostEqual(s.average_waiting, (0 + 5 + 4) / 3)
        self.assertAlmostEqual(s.average_turnaround, (4 + 11 + 7) / 3)
        self.assertAlmostEqual(s.average_response, (0 + 5 + 2) / 3)
        self.assertAlmostEqual(s.throughput, 3 / 12)
        self.assertAlmostEqual(s.service_utilization_pct, 13 / (2 * 12) * 100)
        self.assertAlmostEqual(s.average_memory_wait, (0 + 5 + 1) / 3)
        self.assertEqual((s.completed_count, s.blocked_for_memory_count), (3, 2))

    def test_num_librarians_parameter(self) -> None:
        ms = compute_process_metrics([rr("R1", 0, 4, 0, 4)])
        self.assertAlmostEqual(compute_summary(ms, num_librarians=1).service_utilization_pct, 100.0)
        self.assertAlmostEqual(compute_summary(ms).service_utilization_pct, 50.0)

    def test_empty(self) -> None:
        s = compute_summary([])
        self.assertEqual((s.completed_count, s.throughput), (0, 0.0))


if __name__ == "__main__":
    unittest.main()
