import contextlib
import io
import json
import unittest
from unittest.mock import patch

import test_projects
from app import Invalid, Workbench, handle
from models import FixtureModel, INSTRUCTIONS
from storage import Conflict


class AuditContracts(unittest.TestCase):
    setUp = test_projects.Projects.setUp
    invoice = test_projects.Projects.invoice
    evaluate = test_projects.Projects.evaluate
    def test_complete_amount_grammar(self):
        for i, suffix in enumerate(('12.345', '12.34e2', '12.34.99', '12.34,99', '12.34 USD', '１２.３４')):
            self.model.generate = lambda *a: {'currency': 'USD', 'total_cents': 1234, 'evidence': 'TOTAL USD 12.34'}
            self.assertEqual(self.invoice('TOTAL USD ' + suffix, f'bad{i}')['status'], 'REVIEW_REQUIRED')
        self.model = FixtureModel()
        self.app.model = self.model
        self.assertEqual(self.invoice('ACME. TOTAL USD 12.34', 'good')['data']['total_cents'], 1234)
        self.assertEqual(self.invoice('SUBTOTAL USD 10.00; TOTAL USD 12.34', 'sub')['data']['total_cents'], 1234)
        for i, source in enumerate(('SUBTOTAL USD 12.34', 'TOTAL USD 12.34; TOTAL nope', 'TOTAL USD 12.34\nTOTAL USD 12.34')):
            self.assertEqual(self.invoice(source, f'amb{i}')['status'], 'REVIEW_REQUIRED')

    def test_self_promotion_preserves_distinct_rollback(self):
        self.evaluate('v1'); self.evaluate('v2')
        self.app.run({'action': 'release.promote', 'id': 'v1', 'expected_revision': 0})
        self.app.run({'action': 'release.promote', 'id': 'v2', 'expected_revision': 1})
        again = self.app.run({'action': 'release.promote', 'id': 'v2', 'expected_revision': 2})
        self.assertEqual((again['active'], again['previous'], again['revision']), ('v2', 'v1', 2))
        with self.assertRaises(Conflict):
            self.app.run({'action': 'release.promote', 'id': 'v2', 'expected_revision': 1})
        self.assertEqual(self.app.run({'action': 'release.rollback', 'expected_revision': 2})['active'], 'v1')

    def test_consumer_rejects_changed_prompt_then_uses_explicit_promotion(self):
        self.evaluate('v1')
        self.app.run({'action': 'release.promote', 'id': 'v1', 'expected_revision': 0})
        request = {'action': 'classifier.predict', 'text': 'refund'}
        self.assertEqual(self.app.run(request)['label'], 'billing')
        with patch.dict(INSTRUCTIONS, {'classify': INSTRUCTIONS['classify'] + ' New prompt.'}):
            changed = FixtureModel()
        self.app.model = changed
        with self.assertRaises(Invalid):
            self.app.run(request)
        self.evaluate('v2')
        self.app.run({'action': 'release.promote', 'id': 'v2', 'expected_revision': 1})
        self.assertEqual(self.app.run(request)['release'], 'v2')
        self.app.run({'action': 'release.rollback', 'expected_revision': 2})
        with self.assertRaises(Invalid):
            self.app.run(request)
        self.app.model = self.model
        self.assertEqual(self.app.run(request)['release'], 'v1')

    def test_safe_worker_categories(self):
        private = 'PRIVATE_SOURCE_NEVER_LOG'
        event = {'Records': [
            {'messageId': 'bad', 'body': '{' + private},
            {'messageId': 'review', 'body': json.dumps({'action': 'invoice.extract', 'id': 'review', 'text': private})},
        ]}
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            result = handle(event, self.app, 'worker')
        self.assertEqual(result, {'batchItemFailures': [{'itemIdentifier': 'bad'}]})
        self.assertNotIn(private, output.getvalue())
        events = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual([e['category'] for e in events], ['invalid_input', 'REVIEW_REQUIRED'])
        self.assertEqual([e['retry'] for e in events], [True, False])
