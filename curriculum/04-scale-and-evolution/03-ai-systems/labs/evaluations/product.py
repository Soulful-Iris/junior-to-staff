"""Deterministic tag-suggestion stand-in; intentionally not a model quality benchmark."""
import re
from dataclasses import dataclass

RULES = {'database': ('sql', 'database'), 'frontend': ('css', 'browser'), 'reliability': ('retry', 'timeout')}


def suggest(text, *, allowed, authorized=True):
    if not authorized:
        return []
    words = set(re.findall(r'[a-z]+', text.lower()))
    return sorted(tag for tag, keys in RULES.items() if tag in allowed and words.intersection(keys))


def confusion(labels, predictions):
    """Failure is the positive class. Missing class metrics are None, not 100%."""
    if len(labels) != len(predictions) or any(x not in ('pass','fail') for x in labels+predictions):
        raise ValueError('aligned pass/fail labels required')
    tp=sum(a==b=='fail' for a,b in zip(labels,predictions))
    tn=sum(a==b=='pass' for a,b in zip(labels,predictions))
    fp=sum(a=='pass' and b=='fail' for a,b in zip(labels,predictions))
    fn=sum(a=='fail' and b=='pass' for a,b in zip(labels,predictions))
    return dict(tp=tp,tn=tn,fp=fp,fn=fn,
                agreement=(tp+tn)/len(labels) if labels else None,
                failure_recall=tp/(tp+fn) if tp+fn else None,
                failure_precision=tp/(tp+fp) if tp+fp else None)


@dataclass(frozen=True)
class Outcome:
    kind: str
    latency_ms: int
    tags: tuple = ()


def run_task(outcomes, *, allowed, budget_cents=10, deadline_ms=1000, max_attempts=3):
    """Fake provider charges 4 cents once sent, including timeout/error calls.

    Admission reserves that known per-call cost. Caller enforces a whole-task
    deadline. Real billing, cancellation and concurrent task budgets need their
    own implementation; no provider/network is called here.
    """
    spent=elapsed=attempts=0
    for outcome in outcomes:
        if attempts >= max_attempts or spent+4 > budget_cents or elapsed >= deadline_ms:
            break
        spent += 4
        attempts += 1
        remaining = deadline_ms-elapsed
        elapsed += min(outcome.latency_ms, remaining)
        if outcome.latency_ms > remaining:
            break
        if outcome.kind == 'ok' and set(outcome.tags) <= set(allowed):
            return dict(status='suggestions',tags=list(outcome.tags),spent_cents=spent,elapsed_ms=elapsed,attempts=attempts)
        # Invalid schema/allowlist is terminal. Only transient provider errors retry.
        if outcome.kind != 'transient':
            break
    return dict(status='manual',tags=[],spent_cents=spent,elapsed_ms=elapsed,attempts=attempts)
