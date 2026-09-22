import importlib.util
import json
from pathlib import Path
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

spec=importlib.util.spec_from_file_location('worker',Path(__file__).parent/'src'/'worker.py')
w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w)

class ConditionalFailure(Exception):
    response={'Error':{'Code':'ConditionalCheckFailedException'}}

class FakeDynamo:
    def __init__(self):
        self.items={};self.lock=threading.Lock();self.commits=0;self.lose_response=False
    def put_item(self,**kw):
        key=kw['Item']['operation_id']['S']
        with self.lock:
            if key in self.items: raise ConditionalFailure()
            self.items[key]=kw['Item'];self.commits+=1
            if self.lose_response:
                self.lose_response=False
                raise TimeoutError('committed but response lost')
    def get_item(self,**kw):
        return {'Item':self.items.get(kw['Key']['operation_id']['S'])}

def record(message_id,key='one',numbers=None):
    return {'messageId':message_id,'body':json.dumps({'operation_id':key,'numbers':[1,2] if numbers is None else numbers})}

class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.db=FakeDynamo();self.store=w.DynamoStore(self.db,'test')
    def test_concurrent_duplicates(self):
        with ThreadPoolExecutor(max_workers=8) as pool:
            results=list(pool.map(lambda _: self.store.save('key','digest',3),range(30)))
        self.assertEqual(results.count('created'),1)
        self.assertEqual(self.db.commits,1)
    def test_lost_ack_retry_and_conflict(self):
        self.db.lose_response=True
        self.assertEqual(w.process_batch({'Records':[record('a')]},self.store),{'batchItemFailures':[{'itemIdentifier':'a'}]})
        self.assertEqual(w.process_batch({'Records':[record('b')]},self.store),{'batchItemFailures':[]})
        self.assertEqual(self.db.commits,1)
        self.assertEqual(w.process_batch({'Records':[record('c',numbers=[7])]},self.store),{'batchItemFailures':[{'itemIdentifier':'c'}]})
        self.assertEqual(self.db.items['one']['result']['N'],'3')
    def test_partial_failure(self):
        event={'Records':[record('good'),{'messageId':'bad','body':'invalid'}]}
        self.assertEqual(w.process_batch(event,self.store),{'batchItemFailures':[{'itemIdentifier':'bad'}]})
    def test_domain_validation(self):
        for body in ['[]','{}',json.dumps({'operation_id':'x','numbers':[True]}),json.dumps({'operation_id':'x','numbers':[10**10]})]:
            with self.assertRaises(ValueError):w.parse_job(body)
        self.assertEqual(w.parse_job(json.dumps({'operation_id':'empty','numbers':[]}))[2],0)
    def test_transient_failure_is_not_misclassified(self):
        class Unavailable:
            def put_item(self,**kw): raise RuntimeError('unavailable')
        store=w.DynamoStore(Unavailable(),'test')
        self.assertEqual(w.process_batch({'Records':[record('a')]},store),{'batchItemFailures':[{'itemIdentifier':'a'}]})

if __name__=='__main__':unittest.main()
