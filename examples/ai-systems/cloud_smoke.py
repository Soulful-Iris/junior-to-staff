"""Exercise the SAME project session against a deployed, IAM-protected Lambda."""
import argparse
import json
from uuid import uuid4

from demo import session


class RemoteWorkbench:
    def __init__(self, function):
        import boto3
        from botocore.config import Config
        self.client = boto3.client("lambda", config=Config(read_timeout=200, retries={"total_max_attempts": 1}))
        self.function = function
        self.suffix = "-" + uuid4().hex[:8]

    def run(self, request):
        # Keep immutable IDs unique across smoke runs. Digest values are supplied
        # by the server and must not be rewritten.
        request = dict(request)
        for key in ("id", "order_id", "request_id"):
            if key in request:
                request[key] += self.suffix
        if "expected_revision" in request:
            request["expected_revision"] = self._invoke({"action": "release.get"})["revision"]
        return self._invoke(request)

    def _invoke(self, request):
        response = self.client.invoke(FunctionName=self.function, InvocationType="RequestResponse",
                                      Payload=json.dumps(request).encode())
        body = json.loads(response["Payload"].read())
        if response.get("FunctionError"):
            raise RuntimeError(body)
        return body


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=["assistant", "agent", "extraction", "evaluation"])
    parser.add_argument("--function", required=True)
    args = parser.parse_args()
    print(json.dumps(session(RemoteWorkbench(args.function), args.project), indent=2))
