"""Regressions for Sam's audit findings; run against the real subsystem."""
import io
import unittest
from unittest import mock
import tests
from library_sim.deadlock import PreventionPolicy, run_unsafe_demo
from library_sim.errors import InputError
from library_sim.models import Action, ActionType, ResourceSpec, ReaderSpec
from library_sim.parser import parse_text
from library_sim.resource_parser import validate_actions
from library_sim.resources import ResourceManager
from library_sim.trace import Tracer, EventKind
from library_sim.workers import WorkerPool, ActionBatch


def batches(count):
    """Independent books let every batch acquire/release without virtual waits."""
    return [ActionBatch(f'R{i}',0,(
        Action(f'R{i}',0,ActionType.ACQUIRE,f'OS_BOOK_{i+1}',1,2*i),
        Action(f'R{i}',0,ActionType.RELEASE,f'OS_BOOK_{i+1}',1,2*i+1))) for i in range(count)]


class SamRegressions(unittest.TestCase):
    def test_controlled_overlap_and_waves(self):
        sink=io.StringIO()
        manager=ResourceManager([ResourceSpec(f'OS_BOOK_{i}',1) for i in range(1,6)],PreventionPolicy.ROLLBACK,Tracer(sink))
        with WorkerPool(manager,2) as pool:
            results=pool.run_batches(batches(5))
            self.assertEqual([r.reader_id for r in results],[f'R{i}' for i in range(5)])
            self.assertNotEqual(results[0].thread,results[1].thread)
            self.assertTrue(pool.recorded_overlaps)
        self.assertIn('[overlap]',sink.getvalue())
        self.assertTrue(manager.nothing_held())

    def test_one_worker_single_batch_empty_and_exceptions(self):
        manager=ResourceManager([ResourceSpec('OS_BOOK_1',1)],PreventionPolicy.ROLLBACK,Tracer())
        with WorkerPool(manager,1) as pool:
            self.assertEqual(pool.run_batches([]),[])
            self.assertEqual(pool.run_batches(batches(1))[0].done,2)
            with mock.patch.object(manager,'acquire',side_effect=RuntimeError('worker failed')):
                with self.assertRaisesRegex(RuntimeError,'worker failed'):
                    pool.run_batches(batches(1))

    def test_same_resource_contention(self):
        manager=ResourceManager([ResourceSpec('JOURNAL',1)],PreventionPolicy.ROLLBACK,Tracer())
        requests=[ActionBatch(r,0,(Action(r,0,ActionType.ACQUIRE,'JOURNAL',1,i),)) for i,r in enumerate(('R1','R2'))]
        with WorkerPool(manager,2) as pool:
            results=pool.run_batches(requests)
            self.assertEqual(sum(r.blocked for r in results),1)
            holder=next(r.reader_id for r in results if not r.blocked)
            waiter=next(r.reader_id for r in results if r.blocked)
            self.assertEqual(manager.release(holder,'JOURNAL',1).woken,(waiter,))
            manager.release(waiter,'JOURNAL',2)
        self.assertTrue(manager.nothing_held())

    def test_shared_tracer_isolated_reports(self):
        tracer=Tracer()
        tracer.emit(-1,EventKind.ACQUIRE,'OLD','JOURNAL')
        reports=run_unsafe_demo(tracer=tracer)
        self.assertTrue(reports[0].deadlocked)
        self.assertEqual([r.result.checks.exclusivity_violations for r in reports],[0,0,0])
        for report in reports:
            self.assertEqual(report.events,report.result.trace)
            self.assertTrue(all(e.reader_id != 'OLD' for e in report.events))
        self.assertGreater(len(tracer.events()),len(reports[-1].events))

    def test_descending_offsets_rejected_with_action_line(self):
        text='1\n2\nR1,0,1,6,REGULAR,1,0\n1\nJOURNAL,1\n2\nR1,5,RELEASE,JOURNAL,1\nR1,0,ACQUIRE,JOURNAL,1\n'
        with self.assertRaises(InputError) as ctx:
            parse_text(text,'FINAL')
        self.assertEqual(ctx.exception.line_no,8)
        actions=(Action('R1',5,ActionType.RELEASE,'JOURNAL',1,0),Action('R1',0,ActionType.ACQUIRE,'JOURNAL',1,1))
        with self.assertRaises(InputError):
            validate_actions([ReaderSpec('R1',0,1,6,'REGULAR')],[ResourceSpec('JOURNAL',1)],actions)

    def test_semantic_error_line_and_equal_offsets(self):
        base='1\n2\nR1,0,1,6,REGULAR,1,0\n1\nJOURNAL,1\n2\n'
        with self.assertRaises(InputError) as ctx:
            parse_text(base+'R1,0,RELEASE,JOURNAL,1\nR1,1,ACQUIRE,JOURNAL,1\n','FINAL')
        self.assertEqual(ctx.exception.line_no,7)
        valid=base+'R1,0,ACQUIRE,JOURNAL,1\nR1,0,RELEASE,JOURNAL,1\n'
        self.assertEqual([a.row_index for a in parse_text(valid,'FINAL').actions],[0,1])

    def test_input_order_is_per_reader_not_global(self):
        text = ('2\n2\nR1,0,1,6,REGULAR,1,0\nR2,0,1,6,REGULAR,1,0\n'
                '2\nJOURNAL,1\nREFERENCE_BOOK,1\n4\n'
                'R1,0,ACQUIRE,JOURNAL,1\nR1,2,RELEASE,JOURNAL,1\n'
                'R2,0,ACQUIRE,REFERENCE_BOOK,1\nR2,1,RELEASE,REFERENCE_BOOK,1\n')
        # R2 starts again at offset zero in the file; that is valid.
        self.assertEqual([a.work_offset for a in parse_text(text,'FINAL').actions],[0,2,0,1])

    def test_double_acquire_and_unreleased_diagnostic_lines(self):
        base = '1\n2\nR1,0,1,6,REGULAR,1,0\n1\nJOURNAL,1\n'
        with self.assertRaises(InputError) as ctx:
            parse_text(base+'2\nR1,0,ACQUIRE,JOURNAL,1\nR1,1,ACQUIRE,JOURNAL,1\n','FINAL')
        self.assertEqual(ctx.exception.line_no,8)
        self.assertIn('double-acquired',str(ctx.exception))
        with self.assertRaises(InputError) as ctx:
            parse_text(base+'1\nR1,0,ACQUIRE,JOURNAL,1\n','FINAL')
        self.assertEqual(ctx.exception.line_no,7)
        self.assertIn('still holds',str(ctx.exception))
