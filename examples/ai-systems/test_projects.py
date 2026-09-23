import tempfile
import unittest

from app import Invalid, Workbench, handle
from demo import CASES, session
from models import FixtureModel, ModelUnavailable
from storage import Conflict, LocalStore


class Projects(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = LocalStore(self.tmp.name)
        self.addCleanup(self.store.db.close)
        self.model = FixtureModel()
        self.app = Workbench(self.store, self.model, clock=lambda: 1000)

    def doc(self, readers=None):
        self.app.run({"action": "document.put", "id": "policy", "text": "Refunds within 30 days.", "readers": readers if readers is not None else ["alice"]})

    def ask(self):
        return self.app.run({"action": "assistant.ask", "question": "Refunds?"})

    def order(self):
        self.app.run({"action": "order.put", "id": "o1", "paid_cents": 2000})

    def propose(self, request_id="r1", message="USD 12.50"):
        return self.app.run({"action": "agent.propose", "order_id": "o1", "request_id": request_id, "message": message})

    def approve(self, p):
        return self.app.run({"action": "agent.approve", "order_id": "o1", "request_id": p["request_id"], "digest": p["digest"]})

    def invoice(self, content="TOTAL USD 12.50", record_id="i1"):
        return self.app.run({"action": "invoice.extract", "id": record_id, "text": content})

    def evaluate(self, run_id="v1", cases=None):
        return self.app.run({"action": "evaluation.run", "id": run_id, "cases": CASES if cases is None else cases})

    def test_all_four_complete_sessions(self):
        for project in ("assistant", "agent", "extraction", "evaluation"):
            with self.subTest(project=project):
                self.assertGreaterEqual(len(session(self.app, project)), 4)

    def test_authorization_precedes_model(self):
        self.doc(["bob"])
        self.assertEqual(self.ask()["status"], "NO_EVIDENCE")
        self.assertEqual(self.model.calls, 0)

    def test_revocation_during_model_call(self):
        self.doc()
        generate = self.model.generate
        def race(task, payload):
            self.app.run({"action": "document.revoke", "id": "policy"})
            return generate(task, payload)
        self.model.generate = race
        self.assertEqual(self.ask()["status"], "SOURCE_CHANGED")

    def test_citation_not_in_context_is_rejected(self):
        self.doc()
        self.model.generate = lambda *a: {"citations": ["payroll"]}
        self.assertEqual(self.ask()["status"], "INVALID_MODEL_OUTPUT")

    def test_model_outage_keeps_answer_empty(self):
        self.doc()
        self.model.fault = "outage"
        self.assertEqual(self.ask(), {"status": "MODEL_UNAVAILABLE", "citations": [], "excerpts": []})

    def test_model_malformed_answer_does_not_crash(self):
        self.doc()
        self.model.generate = lambda *a: ["bad"]
        self.assertEqual(self.ask()["status"], "INVALID_MODEL_OUTPUT")

    def test_tenant_cannot_be_selected_from_payload(self):
        with self.assertRaises(Invalid):
            self.app.run({"action": "assistant.ask", "question": "Refund?", "tenant": "team-b"})

    def test_tenants_have_distinct_state(self):
        self.doc()
        other = Workbench(self.store, self.model, tenant="team-b")
        self.assertEqual(other.run({"action": "assistant.ask", "question": "Refunds?"})["status"], "NO_EVIDENCE")

    def test_proposal_does_not_change_balance(self):
        self.order(); self.propose()
        self.assertEqual(self.store.get(self.app.key("order#o1"))[1]["refunded_cents"], 0)

    def test_duplicate_approval_has_one_ledger_effect(self):
        self.order(); p = self.propose()
        first = self.approve(p)
        self.assertEqual(first, self.approve(p))
        self.assertEqual(self.store.get(self.app.key("order#o1"))[1]["refunded_cents"], 1250)

    def test_modified_approval_digest(self):
        self.order(); p = self.propose(); p["digest"] = "wrong"
        with self.assertRaises(Invalid): self.approve(p)

    def test_expired_approval(self):
        self.order(); p = self.propose(); self.app.clock = lambda: 1900
        with self.assertRaises(Invalid): self.approve(p)

    def test_competing_proposals_recheck_balance(self):
        self.order(); p = self.propose(); q = self.propose("r2")
        self.approve(p)
        with self.assertRaises(Invalid): self.approve(q)

    def test_changed_request_cannot_reuse_id(self):
        self.order(); self.propose()
        with self.assertRaises(Conflict): self.propose(message="USD 1.00")

    def test_model_cannot_invent_a_tool(self):
        self.order(); self.model.generate = lambda *a: {"tool": "shell", "amount_cents": 1}
        with self.assertRaises(Invalid): self.propose()

    def test_booleans_are_not_money(self):
        self.order(); self.model.generate = lambda *a: {"tool": "refund", "amount_cents": True}
        with self.assertRaises(Invalid): self.propose()

    def test_invoice_duplicate_avoids_model_call(self):
        first = self.invoice(); self.assertEqual(first, self.invoice())
        self.assertEqual(self.model.calls, 1)

    def test_changed_invoice_id_conflicts(self):
        self.invoice()
        with self.assertRaises(Conflict): self.invoice("TOTAL USD 13.00")

    def test_ambiguous_total_requires_review(self):
        self.assertEqual(self.invoice("TOTAL USD 12.50; TOTAL USD 14.00")["status"], "REVIEW_REQUIRED")

    def test_subtotal_cannot_replace_total(self):
        self.assertEqual(self.invoice("SUBTOTAL USD 12.50; TOTAL USD 14.00")["status"], "REVIEW_REQUIRED")

    def test_missing_currency_requires_review(self):
        self.assertEqual(self.invoice("TOTAL 12.50")["status"], "REVIEW_REQUIRED")

    def test_fabricated_evidence_requires_review(self):
        self.model.generate = lambda *a: {"currency": "USD", "total_cents": 1250, "evidence": "TOTAL USD 12.50"}
        self.assertEqual(self.invoice("TOTAL USD 99.99")["status"], "REVIEW_REQUIRED")

    def test_sqs_only_failed_records_retry(self):
        event = {"Records": [{"messageId": "ok", "body": '{"action":"invoice.extract","id":"i1","text":"TOTAL USD 12.50"}'},
                             {"messageId": "bad", "body": "{"}]}
        self.assertEqual(handle(event, self.app, "worker"), {"batchItemFailures": [{"itemIdentifier": "bad"}]})

    def test_outage_not_saved_as_terminal_invoice(self):
        self.model.fault = "outage"
        with self.assertRaises(ModelUnavailable): self.invoice()
        self.assertIsNone(self.store.get(self.app.key("invoice#i1"))[1])

    def test_sqs_cannot_execute_approvals(self):
        self.assertEqual(handle({"Records": [{"messageId": "x", "body": '{"action":"agent.approve"}'}]}, self.app, "worker"), {"batchItemFailures": [{"itemIdentifier": "x"}]})

    def test_empty_evaluation_is_invalid(self):
        with self.assertRaises(Invalid): self.evaluate(cases=[])

    def test_duplicate_labels_cannot_inflate_evidence(self):
        with self.assertRaises(Invalid): self.evaluate(cases=[CASES[0]]*6)

    def test_missing_category_blocks_release(self):
        cases = [{**CASES[0], "id": f"case-{i}"} for i in range(6)]
        self.assertFalse(self.evaluate(cases=cases)["eligible"])

    def test_severe_misses_block_release(self):
        self.model.fault = "unsafe"
        result = self.evaluate()
        self.assertEqual(result["severe_misses"], 2)
        self.assertFalse(result["eligible"])
        with self.assertRaises(Invalid): self.app.run({"action": "release.promote", "id": "v1", "expected_revision": 0})

    def test_failed_model_is_not_a_passing_evaluation(self):
        self.model.fault = "outage"
        self.assertEqual(self.evaluate()["passed"], 0)

    def test_evaluation_ids_are_immutable(self):
        self.evaluate()
        with self.assertRaises(Conflict): self.evaluate()

    def test_promote_and_rollback_use_revision(self):
        self.evaluate("v1"); self.evaluate("v2")
        self.app.run({"action": "release.promote", "id": "v1", "expected_revision": 0})
        with self.assertRaises(Conflict): self.app.run({"action": "release.promote", "id": "v2", "expected_revision": 0})
        self.app.run({"action": "release.promote", "id": "v2", "expected_revision": 1})
        result = self.app.run({"action": "release.rollback", "expected_revision": 2})
        self.assertEqual((result["active"], result["revision"]), ("v1", 3))

    def test_stale_store_writer_is_rejected(self):
        self.store.put("key", {"value": 1}, 0)
        self.store.put("key", {"value": 2}, 1)
        with self.assertRaises(Conflict): self.store.put("key", {"value": 3}, 1)


if __name__ == "__main__":
    unittest.main()
