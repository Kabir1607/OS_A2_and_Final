"""Contract and unit tests for library_sim.trace (owner: Samar)."""

from __future__ import annotations

import io
import threading
import unittest

import tests  # noqa: F401
from library_sim.models import ResourceSpec
from library_sim.trace import EventKind, TraceEvent, Tracer, audit_exclusivity, format_event


class TraceContract(unittest.TestCase):
    def test_format_event(self) -> None:
        e = TraceEvent(
            seq=17,
            t=3,
            kind=EventKind.BLOCK,
            reader_id="R2",
            resource_id="JOURNAL",
            thread="worker-1",
            detail="held by R1",
        )
        self.assertEqual(format_event(e), "[t=3 #17 worker-1] R2 BLOCK JOURNAL (held by R1)")

    def test_format_event_no_resource_no_detail(self) -> None:
        e = TraceEvent(
            seq=1,
            t=0,
            kind=EventKind.ARRIVE,
            reader_id="R1",
            resource_id=None,
            thread="coordinator",
        )
        self.assertEqual(format_event(e), "[t=0 #1 coordinator] R1 ARRIVE")

    def test_tracer_emit_and_sink(self) -> None:
        buf = io.StringIO()
        tracer = Tracer(sink=buf, enabled=True)
        e1 = tracer.emit(0, EventKind.ARRIVE, "R1")
        e2 = tracer.emit(1, EventKind.ACQUIRE, "R1", "JOURNAL")
        self.assertEqual(e1.seq, 1)
        self.assertEqual(e2.seq, 2)
        events = tracer.events()
        self.assertEqual(len(events), 2)
        lines = buf.getvalue().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertIn("R1 ARRIVE", lines[0])
        self.assertIn("R1 ACQUIRE JOURNAL", lines[1])

    def test_tracer_disabled(self) -> None:
        buf = io.StringIO()
        tracer = Tracer(sink=buf, enabled=False)
        e = tracer.emit(0, EventKind.ARRIVE, "R1")
        self.assertEqual(tracer.events(), [])
        self.assertEqual(buf.getvalue(), "")
        self.assertEqual(e.kind, EventKind.ARRIVE)

    def test_tracer_thread_safety(self) -> None:
        tracer = Tracer(enabled=True)

        def worker(idx: int) -> None:
            for _ in range(100):
                tracer.emit(0, EventKind.ACQUIRE, f"R{idx}", "JOURNAL")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        events = tracer.events()
        self.assertEqual(len(events), 500)
        seqs = [e.seq for e in events]
        self.assertEqual(seqs, list(range(1, 501)))

    def test_audit_exclusivity_clean(self) -> None:
        resources = (ResourceSpec("JOURNAL", 1),)
        events = [
            TraceEvent(1, 0, EventKind.ACQUIRE, "R1", "JOURNAL", "w1"),
            TraceEvent(2, 2, EventKind.RELEASE, "R1", "JOURNAL", "w1"),
            TraceEvent(3, 2, EventKind.HANDOFF, "R2", "JOURNAL", "w2", "from R1"),
            TraceEvent(4, 4, EventKind.RELEASE, "R2", "JOURNAL", "w2"),
        ]
        self.assertEqual(audit_exclusivity(events, resources), 0)

    def test_audit_exclusivity_violations(self) -> None:
        resources = (ResourceSpec("JOURNAL", 1),)
        # R1 acquires, then R2 acquires without R1 releasing -> 1 violation
        # R3 releases without holding -> 1 violation
        events = [
            TraceEvent(1, 0, EventKind.ACQUIRE, "R1", "JOURNAL", "w1"),
            TraceEvent(2, 1, EventKind.ACQUIRE, "R2", "JOURNAL", "w2"),
            TraceEvent(3, 2, EventKind.RELEASE, "R3", "JOURNAL", "w3"),
        ]
        self.assertEqual(audit_exclusivity(events, resources), 2)


if __name__ == "__main__":
    unittest.main()
