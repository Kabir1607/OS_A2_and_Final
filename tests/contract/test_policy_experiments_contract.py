"""Final-only aggregation, safety rejection, and policy ranking checks."""
import dataclasses
import unittest
from unittest import mock
import tests
from library_sim import experiments as exp
from library_sim.deadlock import PreventionPolicy
from library_sim.engine import CheckStats, simulate
from library_sim.models import Allocator, Scheduler
from library_sim.parser import parse_text

SAMPLE=parse_text('1\n2\nR1,0,1,2,REGULAR,1,0\n','FINAL')


class PolicyExperiments(unittest.TestCase):
    def test_mean_min_max_and_ties(self):
        base=exp.run_once(SAMPLE,'sample',Scheduler.FCFS,Allocator.FIRST_FIT,'FINAL')
        observations=[]
        for policy in (PreventionPolicy.ROLLBACK,PreventionPolicy.ORDERED):
            for value in (2.0,4.0):
                observations.append(dataclasses.replace(base,policy=policy,
                                    summary=dataclasses.replace(base.summary,average_waiting=value)))
        with mock.patch.object(exp,'run_once',side_effect=observations):
            rows=exp.compare_policies([('sample',SAMPLE)],schedulers=(Scheduler.FCFS,),repeats=2)
        self.assertEqual(rows[0].average_waiting,exp.Spread(3.0,2.0,4.0))
        winners=exp.better_policy_by_metric(rows)
        self.assertIsNone(winners['sample',Scheduler.FCFS,'average_waiting'])
        rows[1]=dataclasses.replace(rows[1],average_waiting=exp.Spread(1,1,1),throughput=exp.Spread(2,2,2))
        winners=exp.better_policy_by_metric(rows)
        self.assertEqual(winners['sample',Scheduler.FCFS,'average_waiting'],PreventionPolicy.ORDERED)
        self.assertEqual(winners['sample',Scheduler.FCFS,'throughput'],PreventionPolicy.ORDERED)
        self.assertIn('3.000000 [2.000000, 4.000000]',exp.format_markdown(rows))
        almost=dataclasses.replace(rows[0],policy=PreventionPolicy.ORDERED,average_waiting=exp.Spread(3.0005,3,4))
        self.assertIsNone(exp.better_policy_by_metric([rows[0],almost])['sample',Scheduler.FCFS,'average_waiting'])
        with self.assertRaises(ValueError):
            exp.better_policy_by_metric([dataclasses.replace(rows[0],all_safe=False)])

    def test_invalid_repeats_and_unsafe_checks(self):
        with self.assertRaises(ValueError):
            exp.compare_policies([('sample',SAMPLE)],repeats=0)
        result=simulate(SAMPLE,Scheduler.FCFS,Allocator.FIRST_FIT,'FINAL')
        for checks in (None,CheckStats(1,0,1),CheckStats(0,1,1),CheckStats(0,0,0)):
            with mock.patch.object(exp,'simulate',return_value=dataclasses.replace(result,checks=checks)):
                with self.assertRaises(ValueError):
                    exp.run_once(SAMPLE,'unsafe',Scheduler.FCFS,Allocator.FIRST_FIT,'FINAL')
