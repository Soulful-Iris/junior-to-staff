"""Four bounded AI projects. All identities are operator-configured, never model supplied."""
import argparse
import json
import os
from pathlib import Path
import re
import time

from candidate import manifest as candidate_manifest
from invoice_fields import source_total
from models import BedrockModel, FixtureModel, ModelUnavailable
from storage import AwsStore, Conflict, LocalStore, fingerprint


class Invalid(ValueError):
    pass


def text(value, limit=8000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise Invalid("expected nonempty bounded text")
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", value):
        raise Invalid("invalid identifier")
    return value


def cents(value):
    if type(value) is not int or not 0 < value <= 100000:
        raise Invalid("expected integer cents in 1..100000")
    return value


class Workbench:
    def __init__(self, store, model, tenant="team-a", subject="alice", clock=time.time):
        self.store, self.model = store, model
        self.tenant, self.subject, self.clock = identifier(tenant), identifier(subject), clock

    def key(self, name):
        return self.tenant + "#" + name

    def run(self, event):
        if not isinstance(event, dict) or any(k in event for k in ("tenant", "subject", "model_id")):
            raise Invalid("identity and model configuration come from the operator environment")
        action = event.get("action")
        routes = {"document.put": self.document_put, "document.revoke": self.document_revoke,
                  "assistant.ask": self.assistant_ask, "order.put": self.order_put,
                  "agent.propose": self.agent_propose, "agent.approve": self.agent_approve,
                  "invoice.extract": self.invoice_extract, "invoice.get": self.invoice_get,
                  "evaluation.run": self.evaluation_run, "release.promote": self.release_promote,
                  "release.rollback": self.release_rollback, "release.get": self.release_get,
                  "classifier.predict": self.classifier_predict}
        if action not in routes:
            raise Invalid("unknown action")
        return routes[action](event)

    def document_put(self, event):
        doc_id, body = identifier(event.get("id")), text(event.get("text"))
        readers = event.get("readers")
        if not isinstance(readers, list) or len(readers) > 20:
            raise Invalid("readers must be a list of at most 20 subjects")
        readers = sorted(set(identifier(r) for r in readers))
        key = self.key("documents")
        revision, catalog = self.store.get(key)
        catalog = catalog or {}
        if doc_id not in catalog and len(catalog) >= 20:
            raise Invalid("demo catalog limit: 20 documents")
        obj = self.store.write_object({"text": body})
        catalog[doc_id] = {"object": obj, "readers": readers, "version": fingerprint(body)}
        self.store.put(key, catalog, revision)
        return {"id": doc_id, "status": "INDEXED", "version": catalog[doc_id]["version"]}

    def document_revoke(self, event):
        doc_id = identifier(event.get("id"))
        key = self.key("documents")
        revision, catalog = self.store.get(key)
        if not catalog or doc_id not in catalog:
            raise Invalid("document not found")
        catalog[doc_id]["readers"] = []
        self.store.put(key, catalog, revision)
        return {"id": doc_id, "status": "REVOKED"}

    def assistant_ask(self, event):
        question = text(event.get("question"), 500)
        key = self.key("documents")
        revision, catalog = self.store.get(key)
        terms = set(re.findall(r"\w+", question.lower()))
        ranked = []
        for doc_id, doc in (catalog or {}).items():
            if self.subject not in doc["readers"]:
                continue
            body = self.store.read_object(doc["object"])["text"]
            score = len(terms & set(re.findall(r"\w+", body.lower())))
            if score:
                ranked.append((score, doc_id, body[:3000]))
        documents = [{"id": doc_id, "text": body} for _, doc_id, body in sorted(ranked, reverse=True)[:3]]
        if not documents:
            return {"status": "NO_EVIDENCE", "citations": [], "excerpts": []}
        try:
            output = self.model.generate("answer", {"question": question, "documents": documents})
        except ModelUnavailable:
            return {"status": "MODEL_UNAVAILABLE", "citations": [], "excerpts": []}
        citations = output.get("citations") if isinstance(output, dict) else None
        allowed = {d["id"]: d["text"] for d in documents}
        if not isinstance(citations, list) or len(citations) > 3 or any(not isinstance(c, str) or c not in allowed for c in citations):
            return {"status": "INVALID_MODEL_OUTPUT", "citations": [], "excerpts": []}
        # Define the response's authorization decision at this final consistent read.
        # Content already delivered cannot be recalled after a subsequent revocation.
        if self.store.get(key)[0] != revision:
            return {"status": "SOURCE_CHANGED", "citations": [], "excerpts": []}
        citations = list(dict.fromkeys(citations))
        return {"status": "ANSWERED" if citations else "NO_EVIDENCE", "citations": citations,
                "excerpts": [allowed[c] for c in citations], "catalog_revision": revision}

    def order_put(self, event):
        order_id, amount = identifier(event.get("id")), cents(event.get("paid_cents"))
        self.store.put(self.key("order#" + order_id), {"paid_cents": amount, "refunded_cents": 0, "proposals": {}}, 0)
        return {"id": order_id, "status": "CREATED"}

    def agent_propose(self, event):
        order_id, request_id = identifier(event.get("order_id")), identifier(event.get("request_id"))
        message = text(event.get("message"), 1000)
        key = self.key("order#" + order_id)
        revision, order = self.store.get(key)
        if order is None:
            raise Invalid("order not found")
        request_hash = fingerprint(message)
        existing = order["proposals"].get(request_id)
        if existing:
            if existing["request_hash"] != request_hash:
                raise Conflict("request ID reused with changed message")
            return existing
        if len(order["proposals"]) >= 20:
            raise Invalid("demo limit: 20 proposals per order")
        output = self.model.generate("refund", {"message": message})
        if not isinstance(output, dict) or output.get("tool") != "refund":
            raise Invalid("unrecognized model proposal")
        amount = cents(output.get("amount_cents"))
        if amount > order["paid_cents"] - order["refunded_cents"]:
            raise Invalid("proposal exceeds refundable balance")
        proposal = {"order_id": order_id, "request_id": request_id, "amount_cents": amount,
                    "policy": "refund-v1", "expires_at": int(self.clock()) + 900}
        proposal["digest"] = fingerprint(proposal)
        proposal.update(status="PENDING_APPROVAL", request_hash=request_hash)
        order["proposals"][request_id] = proposal
        self.store.put(key, order, revision)
        return proposal

    def agent_approve(self, event):
        order_id, request_id = identifier(event.get("order_id")), identifier(event.get("request_id"))
        key = self.key("order#" + order_id)
        revision, order = self.store.get(key)
        proposal = order and order["proposals"].get(request_id)
        if not proposal or event.get("digest") != proposal["digest"]:
            raise Invalid("approval does not identify this exact proposal")
        if proposal["status"] == "COMMITTED":
            return proposal
        if self.clock() >= proposal["expires_at"]:
            raise Invalid("proposal expired; request a new proposal ID")
        if proposal["amount_cents"] > order["paid_cents"] - order["refunded_cents"]:
            raise Invalid("balance changed; request a new proposal")
        # This is a sandbox ledger, not a real payment provider. Both balance and
        # receipt live in one conditional write, so a crash cannot split them.
        order["refunded_cents"] += proposal["amount_cents"]
        proposal.update(status="COMMITTED", receipt="refund_" + proposal["digest"][:20])
        self.store.put(key, order, revision)
        return proposal

    def invoice_extract(self, event):
        record_id, source = identifier(event.get("id")), text(event.get("text"))
        key = self.key("invoice#" + record_id)
        revision, existing = self.store.get(key)
        source_hash = fingerprint(source)
        if existing:
            if existing["source_hash"] != source_hash:
                raise Conflict("record ID reused with different source")
            return existing
        output = self.model.generate("extract", {"text": source})
        valid = isinstance(output, dict) and output.get("currency") == "USD"
        valid = valid and type(output.get("total_cents")) is int and 0 < output["total_cents"] <= 100000
        total = source_total(source)
        valid = valid and total is not None
        valid = valid and output.get("evidence") == total[0] and output["total_cents"] == total[1]
        result = {"id": record_id, "source_hash": source_hash, "status": "ACCEPTED" if valid else "REVIEW_REQUIRED",
                  "data": output if valid else None, "model": self.model.version, "schema": "invoice-v1"}
        result["artifact"] = self.store.write_object(result)
        self.store.put(key, result, revision)
        return result

    def invoice_get(self, event):
        return self.store.get(self.key("invoice#" + identifier(event.get("id"))))[1] or {"status": "NOT_FOUND"}

    def evaluation_run(self, event):
        run_id = identifier(event.get("id"))
        cases = event.get("cases")
        if not isinstance(cases, list) or not 1 <= len(cases) <= 8:
            raise Invalid("provide 1..8 independent labeled cases")
        ids = set()
        for case in cases:
            if not isinstance(case, dict):
                raise Invalid("case must be an object")
            cid = identifier(case.get("id"))
            text(case.get("text"), 500)
            if cid in ids or case.get("expected") not in ("billing", "technical", "escalate") or type(case.get("severe")) is not bool:
                raise Invalid("duplicate case ID or invalid label/severity")
            ids.add(cid)
        key = self.key("evaluation#" + run_id)
        if self.store.get(key)[1] is not None:
            raise Conflict("evaluation ID is immutable; choose another ID")
        identity = candidate_manifest(self.model)
        results = []
        started = self.clock()
        for case in cases:
            try:
                output = self.model.generate("classify", {"text": case["text"]})
                actual = output.get("label") if isinstance(output, dict) else None
            except ModelUnavailable:
                actual = None
            results.append({"id": case["id"], "expected": case["expected"], "actual": actual,
                            "pass": actual == case["expected"], "severe": case["severe"]})
        if candidate_manifest(self.model) != identity:
            raise Conflict("candidate changed during evaluation; rerun")
        passed = sum(r["pass"] for r in results)
        severe_misses = sum(r["severe"] and not r["pass"] for r in results)
        coverage = {c["expected"] for c in cases} == {"billing", "technical", "escalate"} and any(c["severe"] for c in cases)
        eligible = len(cases) >= 6 and passed == len(cases) and severe_misses == 0 and coverage
        report = {"id": run_id, "candidate": self.model.version, "candidate_manifest": identity,
                  "candidate_id": fingerprint(identity), "dataset_hash": fingerprint(cases),
                  "policy": "demo-gate-v1", "total": len(cases), "passed": passed, "severe_misses": severe_misses,
                  "coverage": coverage, "eligible": eligible, "elapsed_ms": int((self.clock()-started)*1000), "results": results}
        report["artifact"] = self.store.write_object(report)
        self.store.put(key, report, 0)
        return report

    def release_get(self, event):
        revision, state = self.store.get(self.key("release"))
        return {"revision": revision, **(state or {"active": None, "previous": None})}

    def release_promote(self, event):
        report = self.store.get(self.key("evaluation#" + identifier(event.get("id"))))[1]
        if not report or not report["eligible"]:
            raise Invalid("evaluation is absent or blocked")
        revision, state = self.store.get(self.key("release"))
        if type(event.get("expected_revision")) is not int or event["expected_revision"] != revision:
            raise Conflict("release changed; inspect it again")
        if state and state["active"] == report["id"]:
            return {"revision": revision, **state}  # Preserve the previous distinct release.
        state = {"active": report["id"], "previous": state["active"] if state else None}
        new_revision = self.store.put(self.key("release"), state, revision)
        return {"revision": new_revision, **state}

    def release_rollback(self, event):
        revision, state = self.store.get(self.key("release"))
        if not state or not state["previous"]:
            raise Invalid("no previous release")
        if type(event.get("expected_revision")) is not int or event["expected_revision"] != revision:
            raise Conflict("release changed; inspect it again")
        state = {"active": state["previous"], "previous": state["active"]}
        new_revision = self.store.put(self.key("release"), state, revision)
        return {"revision": new_revision, **state}

    def classifier_predict(self, event):
        message = text(event.get("text"), 500)
        revision, release = self.store.get(self.key("release"))
        report = release and self.store.get(self.key("evaluation#" + release["active"]))[1]
        identity = candidate_manifest(self.model)
        if (not report or not report.get("eligible")
                or report.get("candidate_manifest") != identity
                or report.get("candidate_id") != fingerprint(identity)):
            raise Invalid("active release does not authorize this candidate; evaluate or load matching code")
        output = self.model.generate("classify", {"text": message})
        if (candidate_manifest(self.model) != identity
                or self.store.get(self.key("release"))[0] != revision):
            raise Conflict("release or candidate changed during inference; retry")
        if not isinstance(output, dict) or output.get("label") not in ("billing", "technical", "escalate"):
            raise Invalid("invalid classification")
        return {"label": output["label"], "release": report["id"], "candidate_id": report["candidate_id"]}


def configured():
    tenant, subject = os.getenv("AI_TENANT", "team-a"), os.getenv("AI_SUBJECT", "alice")
    store = AwsStore(os.environ["STATE_TABLE"], os.environ["ARTIFACT_BUCKET"], tenant) if "STATE_TABLE" in os.environ else LocalStore(os.getenv("AI_STATE", ".ai-state"))
    model = BedrockModel(os.environ["BEDROCK_MODEL_ID"]) if os.getenv("AI_MODEL_MODE", "fixture") == "bedrock" else FixtureModel()
    return Workbench(store, model, tenant, subject)


def handle(event, workbench, surface="operator"):
    if surface == "worker":
        failures = []
        for record in event.get("Records", []):
            payload = None
            try:
                payload = json.loads(record["body"])
                if not isinstance(payload, dict) or payload.get("action") != "invoice.extract":
                    raise Invalid("worker only accepts invoice extraction")
                result = workbench.run(payload)
                print(json.dumps({"event": "invoice_worker", "message_ref": fingerprint(record["messageId"])[:16],
                                  "category": result["status"], "retry": False}))
            except Exception as exc:
                category = ("invalid_input" if isinstance(exc, (Invalid, ValueError, KeyError, TypeError)) else
                            "id_conflict" if isinstance(exc, Conflict) else
                            "provider_unavailable" if isinstance(exc, ModelUnavailable) else "processing_failure")
                # No exception text, source, prompt, or model output enters logs.
                # Invalid jobs also fail the batch: SQS redrive sends them to DLQ,
                # instead of silently acknowledging a request with no durable result.
                print(json.dumps({"event": "invoice_worker", "message_ref": fingerprint(record["messageId"])[:16],
                                  "category": category, "retry": True, "disposition": "redrive"}))
                failures.append({"itemIdentifier": record["messageId"]})
        return {"batchItemFailures": failures}
    return workbench.run(event)


def handler(event, context):
    return handle(event, configured(), os.getenv("AI_SURFACE", "operator"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("request", type=Path, help="JSON request file")
    args = parser.parse_args()
    try:
        print(json.dumps(handler(json.loads(args.request.read_text()), None), indent=2))
    except (Invalid, Conflict, ModelUnavailable) as exc:
        print(json.dumps({"error": type(exc).__name__, "message": str(exc)}))
        raise SystemExit(1)
