"""Allocator experiments work with only A2 modules installed."""
import dataclasses
import io
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock
from tests import REPO_ROOT
from library_sim import experiments as exp
from library_sim.engine import simulate
from library_sim.models import Allocator, Scheduler
from library_sim.parser import parse_text, parse_file

SAMPLE=parse_text('1\n2\nR1,0,1,2,REGULAR,1,0\n','A2')


class AllocatorExperiments(unittest.TestCase):
    def test_six_rows_and_distinguishing_workload(self):
        rows=exp.compare_allocators(parse_file(str(REPO_ROOT/'inputs/a2/comparison.txt'),'A2'),'comparison')
        self.assertEqual(len(rows),6)
        self.assertEqual([r.pool.max_ext_frag for r in rows[:3]],[2,0,1])
        self.assertTrue(all(r.policy is None and r.total_resource_wait == 0 for r in rows))
        text=exp.format_markdown(rows)
        self.assertIn('average_memory_wait',text)
        self.assertIn('max_ext_frag',text)
        self.assertEqual(len(text.splitlines()),8)
        self.assertEqual(exp.format_markdown([]),'')

    def test_rejects_unfinished_and_duplicate_results(self):
        result=simulate(SAMPLE,Scheduler.FCFS,Allocator.FIRST_FIT,'A2')
        for bad in (dataclasses.replace(result,incomplete=('R1',)),
                    dataclasses.replace(result,readers=()),
                    dataclasses.replace(result,readers=result.readers*2)):
            with mock.patch.object(exp,'simulate',return_value=bad),self.assertRaises(ValueError):
                exp.run_once(SAMPLE,'bad',Scheduler.FCFS,Allocator.FIRST_FIT,'A2')

    def test_cli_report_and_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'comparison.md'
            self.assertEqual(exp.main(['allocators',str(REPO_ROOT/'inputs/a2/comparison.txt'),'--md',str(output)]),0)
            self.assertIn('WORST_FIT',output.read_text())
            for argv in ([],['allocators','missing.txt'],['policies','missing.txt','--repeats','0']):
                stderr=io.StringIO()
                with redirect_stderr(stderr):
                    self.assertEqual(exp.main(argv),1)
                self.assertTrue(stderr.getvalue().startswith('Error:'))
