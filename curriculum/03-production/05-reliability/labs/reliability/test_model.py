import unittest
import csv
from pathlib import Path
from fractions import Fraction as F
from model import sli, burn, alarm, latched, leaf_attempts, retry_allowed, admit, capacity, drain


class ReliabilityTests(unittest.TestCase):
    def test_incident_csv_windows_and_observed_queue(self):
        with (Path(__file__).parent/'incident.csv').open() as f:
            rows=[{k:int(v) for k,v in row.items()} for row in csv.DictReader(f)]
        def window(start,end):
            return [(r['good_reads'],r['eligible_reads']) for r in rows[start:end+1]]
        self.assertEqual(burn(window(3,4)),45)
        self.assertEqual(burn(window(0,4)),22)
        self.assertTrue(alarm(burn(window(3,4)),burn(window(0,4))))
        self.assertEqual(burn(window(5,6)),0)
        self.assertEqual(burn(window(2,6)),22)
        self.assertFalse(alarm(burn(window(5,6)),burn(window(2,6))))
        for previous,current in zip(rows,rows[1:]):
            growth=(current['offered_attempts_per_s']-current['completed_attempts_per_s'])*60
            self.assertEqual(current['queue_items']-previous['queue_items'],growth)
        self.assertEqual(drain(rows[5]['queue_items'],80,100),1020)

    def test_variable_traffic_budget_not_minutes(self):
        rows = [(990000, 990000), (0, 10000)]
        self.assertEqual(sli(rows), F(99,100))
        self.assertEqual(burn(rows), 10)
        self.assertNotEqual(sli(rows), F(1,2))  # averaging interval ratios is wrong
        self.assertEqual(F(30*24*60,1000), F(216,5))  # 43.2 time-based minutes only

    def test_no_eligible_requests_and_invalid_counters(self):
        self.assertIsNone(sli([(0,0)]))
        self.assertIsNone(burn([]))
        self.assertIsNone(alarm(None,20))
        self.assertFalse(alarm(None,0))
        with self.assertRaises(ValueError):
            sli([(2,1)])

    def test_boolean_recovery_both_directions_and_latch(self):
        self.assertTrue(alarm(20,20))
        self.assertFalse(alarm(0,20))
        self.assertFalse(alarm(20,0))
        self.assertFalse(alarm(0,0))
        self.assertTrue(latched(True,False,True))
        self.assertTrue(latched(True,True,False))
        self.assertFalse(latched(True,False,False))
        self.assertFalse(latched(False,False,True))

    def test_attempt_units_and_layer_scope(self):
        self.assertEqual(leaf_attempts([3,3,3]),27)
        self.assertEqual(leaf_attempts([3,3,3],counts='retries'),64)
        self.assertEqual(leaf_attempts([1,3,1]),3)
        self.assertEqual(100+20*20,500)  # per-process is not global retry budget

    def test_priority_cannot_create_capacity(self):
        a=admit(120,30,100)
        self.assertEqual((a.critical,a.bulk,a.critical_refused,a.bulk_refused),(100,0,20,30))
        a=admit(80,40,100)
        self.assertEqual((a.critical,a.bulk,a.critical_refused,a.bulk_refused),(80,20,0,20))

    def test_retry_policy_has_countermodels(self):
        p=dict(safe=True,remaining_ms=1500,wait_ms=1000,attempt_ms=500,tokens=1)
        self.assertTrue(retry_allowed(429,**p))
        for status in (400,401,403,404,422):
            self.assertFalse(retry_allowed(status,**p))
        for changed in ({'safe':False},{'tokens':0},{'remaining_ms':1499}):
            self.assertFalse(retry_allowed(429,**(p|changed)))

    def test_queue_growth_recovery_and_closed_loop(self):
        self.assertEqual(capacity(20,.2),100)
        self.assertEqual(capacity(20,2),10)
        backlog=(80-10)*60
        self.assertEqual(backlog,4200)
        self.assertEqual(drain(backlog,80,100),210)
        self.assertIsNone(drain(backlog,100,100))
        self.assertEqual(capacity(20,2),10)  # 20 closed-loop clients self-throttle to 10/s
        self.assertEqual((80-capacity(20,2))*60,4200)  # open arrivals still accumulate


if __name__=='__main__':
    unittest.main(verbosity=2)
