"""A6: immutable golden exports, independent arithmetic, and complete runs."""
import unittest
from tests import REPO_ROOT
from tests.reference_a2 import reference
from library_sim.engine import Simulation
from library_sim.metrics import compute_process_metrics, compute_summary
from library_sim.models import Allocator, Scheduler, State
from library_sim.output import format_a2
from library_sim.parser import parse_file


class A2Fixtures(unittest.TestCase):
    def test_every_golden_export_and_repeat(self):
        """Check all 54 exports; re-running must not change even one byte."""
        cases = sorted((REPO_ROOT/'inputs/a2').glob('*.txt'))
        self.assertEqual(len(cases),9)
        for path in cases:
            for scheduler in Scheduler:
                for allocator in Allocator:
                    with self.subTest(input=path.name,scheduler=scheduler,allocator=allocator):
                        expected=(REPO_ROOT/'tests/expected/a2'/f'{path.stem}_{scheduler.value}_{allocator.value}.out').read_text()
                        self.assertEqual(reference(path.read_text(),scheduler.value,allocator.value)['text'],expected)
                        for _ in range(2):
                            sim=Simulation(parse_file(str(path),'A2'),scheduler,allocator,mode='A2')
                            result=sim.run()
                            metrics=compute_process_metrics(result.readers)
                            self.assertEqual(format_a2(metrics,compute_summary(metrics),result.pool),expected)
                            self.assertEqual(sim.pool.occupied,0)
                            self.assertEqual(result.incomplete,())
                            self.assertTrue(all(r.state is State.TERMINATED for r in sim.readers.values()))

    def test_hand_calculated_small_case_anchors(self):
        """These constants were derived by tracing seats/librarians by hand."""
        # Values per reader are (M,S,C); last entries are (seat-time, peak, max F_ext).
        cases={
            'initial_idle': ({'R1':(5,5,8)},(6,2,0)),
            'head_of_line': ({'R1':(0,0,4),'R2':(4,4,6),'R3':(4,4,5)},(23,4,0)),
            'completion_arrival': ({'R1':(0,0,3),'R2':(0,0,3),'R3':(3,3,5),'R4':(5,5,6)},(31,6,0)),
            'request_bounds': ({'R1':(0,0,2),'R2':(2,2,3),'R3':(2,2,4)},(15,6,1)),
            'fragmented_wait': ({'R1':(0,0,2),'R2':(0,0,6),'R3':(0,2,4),'R4':(6,6,7)},(27,6,2)),
            'equal_holes_coalescing': ({'R1':(0,0,2),'R2':(0,0,6),'R3':(0,2,4),'R4':(4,4,5),'R5':(4,5,6)},(27,6,1)),
            'long_idle_gap': ({'R1':(0,0,2),'R2':(20,20,21),'R3':(25,25,27)},(12,6,0)),
        }
        for name,(timings,totals) in cases.items():
            for scheduler in Scheduler:
                for allocator in Allocator:
                    result=reference((REPO_ROOT/'inputs/a2'/f'{name}.txt').read_text(),scheduler.value,allocator.value)
                    self.assertEqual({v[0]:(v[9],v[4],v[5]) for v in result['records']},timings,name)
                    self.assertEqual((result['integral'],result['peak'],result['frag']),totals,name)
        path=REPO_ROOT/'inputs/a2/simultaneous_arrivals.txt'
        for allocator in Allocator:
            fcfs=reference(path.read_text(),'FCFS',allocator.value)
            priority=reference(path.read_text(),'PRIORITY',allocator.value)
            self.assertEqual({v[0]:(v[9],v[4],v[5]) for v in fcfs['records']},
                             {'R1':(0,0,3),'R10':(0,0,2),'R2':(0,2,4)})
            self.assertEqual({v[0]:(v[9],v[4],v[5]) for v in priority['records']},
                             {'R1':(0,2,5),'R10':(0,0,2),'R2':(0,0,2)})
            # At t=3 only seat 2 remains reserved: free runs 0-1 and 3-5 give F=2.
            self.assertEqual((fcfs['integral'],fcfs['frag']),(9,2))
            self.assertEqual((priority['integral'],priority['frag']),(9,0))
