import json
from pathlib import Path
import unittest
from product import suggest, confusion, run_task, Outcome

BASE=Path(__file__).parent
CASES=json.loads((BASE/'regression.json').read_text())


def mismatches(implementation):
    return [case['id'] for case in CASES if implementation(case['text'],allowed=case['allowed'],authorized=case['authorized']) != case['expected']]


class EvaluationTests(unittest.TestCase):
    def test_all_required_regressions_pass(self):
        self.assertEqual(len(CASES),20)
        self.assertEqual(mismatches(suggest),[])

    def test_seeded_defects_are_detected(self):
        def no_auth(text,**kwargs):
            return suggest(text,**(kwargs|{'authorized':True}))
        def ignore_allowlist(text,**kwargs):
            return suggest(text,**(kwargs|{'allowed':['database','frontend','reliability']}))
        def constant(text,**kwargs):
            return ['database']
        self.assertEqual(mismatches(no_auth),['r20'])
        self.assertEqual(mismatches(ignore_allowlist),['r18','r19'])
        self.assertGreater(len(mismatches(constant)),10)

    def test_majority_judge_counterexample(self):
        m=confusion(['pass']*99+['fail'],['pass']*100)
        self.assertEqual((m['tp'],m['tn'],m['fp'],m['fn']),(0,99,0,1))
        self.assertEqual(m['agreement'],.99)
        self.assertEqual(m['failure_recall'],0)
        self.assertIsNone(m['failure_precision'])
        self.assertIsNone(confusion([],[])['agreement'])

    def test_heldout_matrix_and_severity(self):
        row=json.loads((BASE/'heldout-labels.json').read_text())
        m=confusion(row['labels'],row['predictions'])
        self.assertEqual((m['tp'],m['tn'],m['fp'],m['fn']),(3,14,2,1))
        self.assertEqual(m['failure_recall'],.75)
        self.assertEqual(m['failure_precision'],.6)
        missed=sum(w for label,pred,w in zip(row['labels'],row['predictions'],row['severity']) if label=='fail' and pred=='pass')
        self.assertEqual(missed,10)  # the only miss is the most severe failure

    def test_budget_and_outage_fallback(self):
        r=run_task([Outcome('transient',100)]*10,allowed=['database'])
        self.assertEqual(r,dict(status='manual',tags=[],spent_cents=8,elapsed_ms=200,attempts=2))
        r=run_task([Outcome('ok',100,('database',))],allowed=['database'],budget_cents=3)
        self.assertEqual((r['attempts'],r['spent_cents']),(0,0))

    def test_whole_task_deadline_and_output_boundary(self):
        r=run_task([Outcome('transient',700),Outcome('ok',700,('database',))],allowed=['database'])
        self.assertEqual((r['status'],r['elapsed_ms'],r['spent_cents']),('manual',1000,8))
        r=run_task([Outcome('ok',10,('private-tenant-tag',))],allowed=['database'])
        self.assertEqual((r['status'],r['tags']),('manual',[]))
        r=run_task([Outcome('transient',100),Outcome('ok',100,('database',))],allowed=['database'])
        self.assertEqual((r['status'],r['tags'],r['spent_cents']),('suggestions',['database'],8))


if __name__=='__main__':
    unittest.main(verbosity=2)
