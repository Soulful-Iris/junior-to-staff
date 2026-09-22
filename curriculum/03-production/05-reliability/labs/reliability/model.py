"""Constructed deterministic models: no network, scheduler, SDK, or AWS service."""
from dataclasses import dataclass
from fractions import Fraction
from math import prod


def sli(rows):
    """Rows are (good, eligible); no traffic is unknown, never 100% success."""
    rows = list(rows)
    if any(g < 0 or n < 0 or g > n for g, n in rows):
        raise ValueError('require 0 <= good <= eligible')
    n = sum(n for _, n in rows)
    return Fraction(sum(g for g, _ in rows), n) if n else None


def burn(rows, objective=Fraction(999, 1000)):
    if not 0 < objective < 1:
        raise ValueError('objective must be between zero and one')
    ratio = sli(rows)
    return None if ratio is None else (1 - ratio) / (1 - objective)


def alarm(short, long, threshold=Fraction(144, 10)):
    """Three-valued AND. False clears; missing with no false is unknown."""
    states = [None if x is None else x >= threshold for x in (short, long)]
    if False in states:
        return False
    return None if None in states else True


def latched(previous, short_alarm, long_alarm):
    """Separate teaching policy: trigger on both, hold until both recover."""
    return (short_alarm or long_alarm) if previous else (short_alarm and long_alarm)


def leaf_attempts(limits, *, counts='attempts'):
    if counts not in ('attempts', 'retries'):
        raise ValueError('name the unit')
    if any(type(n) is not int or n < (1 if counts == 'attempts' else 0) for n in limits):
        raise ValueError('invalid count')
    return prod(n + (counts == 'retries') for n in limits)


def retry_allowed(status, *, safe, remaining_ms, wait_ms, attempt_ms, tokens):
    """Toy GET/idempotent policy; server wait honored only inside total deadline."""
    transient = status in (429, 502, 503, 504)
    return (transient and safe and tokens > 0 and wait_ms >= 0 and attempt_ms > 0
            and remaining_ms >= wait_ms + attempt_ms)


@dataclass
class Admission:
    critical: int
    bulk: int
    critical_refused: int
    bulk_refused: int


def admit(critical, bulk, capacity):
    if min(critical, bulk, capacity) < 0:
        raise ValueError('negative demand')
    c = min(critical, capacity)
    b = min(bulk, capacity - c)
    return Admission(c, b, critical-c, bulk-b)


def capacity(slots, seconds):
    if slots < 0 or seconds <= 0:
        raise ValueError('invalid capacity inputs')
    return Fraction(slots) / Fraction(str(seconds))


def drain(backlog, incoming, service):
    """Ideal fluid model. None means no finite drain while fresh arrivals continue."""
    if min(backlog, incoming, service) < 0:
        raise ValueError('negative work')
    return Fraction(0) if backlog == 0 else (Fraction(backlog, service-incoming) if service > incoming else None)
