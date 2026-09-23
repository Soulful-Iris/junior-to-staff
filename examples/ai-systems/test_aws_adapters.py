"""Optional AWS adapter tests with mocked services; not a live cloud smoke test."""
import unittest

try:
    import boto3
    from moto import mock_aws
except ImportError:
    boto3 = None

from app import Workbench
from demo import session
from models import BedrockModel, FixtureModel
from storage import AwsStore, Conflict


@unittest.skipUnless(boto3, "install requirements-test.txt for AWS adapter tests")
class AwsAdapters(unittest.TestCase):
    def setUp(self):
        self.mock = mock_aws()
        self.mock.start()
        self.addCleanup(self.mock.stop)
        import os
        from unittest.mock import patch
        env = patch.dict(os.environ, {"AWS_DEFAULT_REGION": "us-east-1"})
        env.start(); self.addCleanup(env.stop)
        boto3.client("dynamodb").create_table(TableName="test-state", BillingMode="PAY_PER_REQUEST",
            AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}])
        boto3.client("s3").create_bucket(Bucket="ai-project-artifacts")
        self.store = AwsStore("test-state", "ai-project-artifacts", "team-a")

    def test_all_sessions_with_aws_persistence_contract(self):
        app = Workbench(self.store, FixtureModel(), clock=lambda: 1000)
        for project in ("assistant", "agent", "extraction", "evaluation"):
            self.assertGreaterEqual(len(session(app, project)), 4)

    def test_conditional_write_rejects_stale_revision(self):
        self.store.put("team-a#test", {"x": 1}, 0)
        with self.assertRaises(Conflict): self.store.put("team-a#test", {"x": 2}, 0)
        self.store.put("team-a#test", {"x": 2}, 1)
        with self.assertRaises(Conflict): self.store.put("team-a#test", {"x": 3}, 1)

    def test_objects_enforce_tenant_prefix(self):
        key = self.store.write_object({"amount": 1250})
        self.assertEqual(self.store.read_object(key), {"amount": 1250})
        with self.assertRaises(ValueError): self.store.read_object("team-b/secret.json")

    def test_converse_adapter_uses_documented_request(self):
        from botocore.stub import Stubber
        model = BedrockModel("test-model")
        reply = {"output": {"message": {"role": "assistant", "content": [{"text": '{"label":"billing"}'}]}},
                 "stopReason": "end_turn", "usage": {"inputTokens": 4, "outputTokens": 5, "totalTokens": 9},
                 "metrics": {"latencyMs": 10}}
        with Stubber(model.client) as stub:
            stub.add_response("converse", reply)
            self.assertEqual(model.generate("classify", {"text": "refund"}), {"label": "billing"})
            stub.assert_no_pending_responses()


if __name__ == "__main__":
    unittest.main()
