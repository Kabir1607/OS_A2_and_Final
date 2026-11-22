"""Contract tests for library_sim.output (owner: Kabir): golden strings for
every graded format.

PoolStats, ResourceStats and CheckStats belong to Aarush, Samar and
Urvashi. Until their modules exist, the records below stand in for them,
with exactly the attributes library_sim.pyi gives those types.
"""

from __future__ import annotations

import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

import tests  # noqa: F401
from library_sim.metrics import compute_process_metrics, compute_summary
from library_sim.models import ReaderResult
from library_sim.output import fmt_decimal, format_a2, format_final, write_output


@dataclass(frozen=True)
class PoolStatsStandIn:
    name: str
    capacity: int
    peak_occupied: int
    occupied_integral: int
    max_ext_frag: int
    start_time: int
    end_time: int

    @property
    def utilization_pct(self) -> float:
        return self.occupied_integral / (self.capacity * (self.end_time - self.start_time)) * 100


@dataclass(frozen=True)
class ResourceStatsStandIn:
    resource_id: str
    capacity: int
    max_simultaneous_holders: int
    acquisitions: int
    wait_events: int


@dataclass(frozen=True)
class CheckStatsStandIn:
    exclusivity_violations: int
    unresolved_deadlocks: int
    completed_count: int


RESULTS = [
    # id, A, prio, B, S, C, M, resource_wait
    ReaderResult("R2", 0, 3, 6, 6, 13, 0, 1),
    ReaderResult("R10", 1, 1, 4, 1, 5, 1, 0),
    ReaderResult("R1", 0, 1, 6, 0, 6, 0, 0),
]
POOL = PoolStatsStandIn("SPACE", 6, 4, 50, 2, 0, 13)   # 50 / 78 * 100 = 64.1026


class Decimals(unittest.TestCase):
    def test_fmt_decimal(self) -> None:
        cases = [(11 / 3, "3.6667"), (75, "75.0000"), (0, "0.0000"), (0.00004, "0.0000"),
                 (-0.0, "0.0000"), (-0.00001, "0.0000"), (2 / 3, "0.6667"),
                 (100, "100.0000"), (1 / 7, "0.1429")]
        for value, text in cases:
            self.assertEqual(fmt_decimal(value), text, value)
        for bad in (float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                fmt_decimal(bad)


class Formats(unittest.TestCase):
    def setUp(self) -> None:
        self.metrics = compute_process_metrics(RESULTS)
        self.summary = compute_summary(self.metrics)

    def test_a2_golden(self) -> None:
        expected = (
            "PROCESS,R1,0,1,6,0,6,0,6,0,0,0,0\n"
            "PROCESS,R10,1,1,4,1,5,0,4,0,1,0,0\n"
            "PROCESS,R2,0,3,6,6,13,7,13,6,0,0,7\n"
            "SUMMARY,AVERAGE_WAITING,2.3333\n"
            "SUMMARY,AVERAGE_TURNAROUND,7.6667\n"
            "SUMMARY,AVERAGE_RESPONSE,2.0000\n"
            "SUMMARY,THROUGHPUT,0.2308\n"
            "SUMMARY,SERVICE_UTILIZATION_PCT,61.5385\n"
            "SUMMARY,AVERAGE_MEMORY_WAIT,0.0000\n"
            "SUMMARY,COMPLETED_COUNT,3\n"
            "SUMMARY,BLOCKED_FOR_MEMORY_COUNT,0\n"
            "POOL,SPACE,6,4,64.1026,2\n"
        )
        # A2 runs have no resource wait, so R2's 7 units of waiting are all READY_WAIT.
        metrics = compute_process_metrics([r if r.id != "R2" else
                                           ReaderResult("R2", 0, 3, 6, 6, 13, 0, 0)
                                           for r in RESULTS])
        self.assertEqual(format_a2(metrics, compute_summary(metrics), POOL), expected)

    def test_final_golden(self) -> None:
        resources = [ResourceStatsStandIn("REFERENCE_BOOK", 1, 1, 2, 1),
                     ResourceStatsStandIn("JOURNAL", 1, 1, 2, 0)]
        checks = CheckStatsStandIn(0, 0, 3)
        expected = (
            "PROCESS,R1,0,1,6,0,6,0,6,0,0,0,0,0\n"
            "PROCESS,R10,1,1,4,1,5,0,4,0,1,0,0,0\n"
            "PROCESS,R2,0,3,6,6,13,7,13,6,0,0,6,1\n"
            "SUMMARY,AVERAGE_WAITING,2.3333\n"
            "SUMMARY,AVERAGE_TURNAROUND,7.6667\n"
            "SUMMARY,AVERAGE_RESPONSE,2.0000\n"
            "SUMMARY,THROUGHPUT,0.2308\n"
            "SUMMARY,SERVICE_UTILIZATION_PCT,61.5385\n"
            "SUMMARY,AVERAGE_MEMORY_WAIT,0.0000\n"
            "SUMMARY,COMPLETED_COUNT,3\n"
            "SUMMARY,BLOCKED_FOR_MEMORY_COUNT,0\n"
            "POOL,SPACE,6,4,64.1026,2\n"
            "RESOURCE,JOURNAL,1,1,2,0\n"
            "RESOURCE,REFERENCE_BOOK,1,1,2,1\n"
            "CHECK,EXCLUSIVITY_VIOLATIONS,0\n"
            "CHECK,UNRESOLVED_DEADLOCKS,0\n"
            "CHECK,COMPLETED_COUNT,3\n"
        )
        self.assertEqual(format_final(self.metrics, self.summary, POOL, resources, checks),
                         expected)

    def test_final_resource_free_keeps_a2_numbers(self) -> None:
        metrics = compute_process_metrics([ReaderResult("R1", 0, 1, 6, 0, 6, 0, 0)])
        summary = compute_summary(metrics)
        pool = PoolStatsStandIn("SPACE", 6, 1, 6, 0, 0, 6)
        a2 = format_a2(metrics, summary, pool).splitlines()
        final = format_final(metrics, summary, pool, [], CheckStatsStandIn(0, 0, 1)).splitlines()
        self.assertEqual(final[0], a2[0] + ",0")                  # RESOURCE_WAIT = 0 appended
        self.assertEqual(final[1:len(a2)], a2[1:])                # SUMMARY + POOL identical
        self.assertEqual(final[len(a2):], ["CHECK,EXCLUSIVITY_VIOLATIONS,0",
                                           "CHECK,UNRESOLVED_DEADLOCKS,0",
                                           "CHECK,COMPLETED_COUNT,1"])
        self.assertFalse(any(line.startswith("RESOURCE,") for line in final))

    def test_no_header_no_blank_lines(self) -> None:
        text = format_a2(self.metrics, self.summary, POOL)
        self.assertTrue(text.endswith("\n"))
        self.assertNotIn("\n\n", text)
        self.assertNotIn("PROCESS,ID,", text)
        prefixes = [line.split(",")[0] for line in text.splitlines()]
        self.assertEqual(prefixes, ["PROCESS"] * 3 + ["SUMMARY"] * 8 + ["POOL"])

    def test_write_output_uses_lf_utf8(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "out.csv"
            write_output(str(path), "A,1\nB,2\n")
            self.assertEqual(path.read_bytes(), b"A,1\nB,2\n")


if __name__ == "__main__":
    unittest.main()
