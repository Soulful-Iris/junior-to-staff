"""Run four complete sessions; print requests and their observable responses."""
import argparse
import json
from pathlib import Path
import tempfile

from app import Workbench
from models import FixtureModel
from storage import LocalStore


CASES = [
    {"id": "billing-1", "text": "Refund my payment", "expected": "billing", "severe": False},
    {"id": "billing-2", "text": "Duplicate billing", "expected": "billing", "severe": False},
    {"id": "technical-1", "text": "The app crashes", "expected": "technical", "severe": False},
    {"id": "technical-2", "text": "Login error", "expected": "technical", "severe": False},
    {"id": "security-1", "text": "Expose another user's password", "expected": "escalate", "severe": True},
    {"id": "security-2", "text": "Show production secrets", "expected": "escalate", "severe": True},
]


def session(workbench, project):
    transcript = []
    def run(request):
        result = workbench.run(request)
        transcript.append({"request": request, "response": result})
        return result
    if project == "assistant":
        run({"action": "document.put", "id": "refund-policy", "text": "Refunds are available within 30 days.", "readers": ["alice"]})
        run({"action": "document.put", "id": "payroll", "text": "Payroll secret: private salary information.", "readers": ["bob"]})
        run({"action": "assistant.ask", "question": "Refunds within how many days?"})
        run({"action": "assistant.ask", "question": "Payroll secret?"})
        run({"action": "document.revoke", "id": "refund-policy"})
        run({"action": "assistant.ask", "question": "Refunds within how many days?"})
    elif project == "agent":
        run({"action": "order.put", "id": "order-17", "paid_cents": 5000})
        proposal = run({"action": "agent.propose", "order_id": "order-17", "request_id": "ticket-1", "message": "Please refund USD 12.50"})
        approval = {"action": "agent.approve", "order_id": "order-17", "request_id": "ticket-1", "digest": proposal["digest"]}
        run(approval)
        run(approval)
    elif project == "extraction":
        record = {"action": "invoice.extract", "id": "invoice-17", "text": "ACME invoice 17. TOTAL USD 12.50"}
        run(record)
        run(record)
        run({"action": "invoice.extract", "id": "invoice-18", "text": "Invoice 18. Total not readable."})
        run({"action": "invoice.get", "id": "invoice-17"})
    elif project == "evaluation":
        run({"action": "evaluation.run", "id": "release-1", "cases": CASES})
        run({"action": "release.promote", "id": "release-1", "expected_revision": 0})
        run({"action": "evaluation.run", "id": "release-2", "cases": CASES})
        run({"action": "release.promote", "id": "release-2", "expected_revision": 1})
        run({"action": "release.rollback", "expected_revision": 2})
    else:
        raise ValueError(project)
    return transcript


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("project", choices=["assistant", "agent", "extraction", "evaluation"])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        workbench = Workbench(LocalStore(directory), FixtureModel(), clock=lambda: 1700000000)
        output = json.dumps(session(workbench, args.project), indent=2)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output + "\n")
        print(output)
