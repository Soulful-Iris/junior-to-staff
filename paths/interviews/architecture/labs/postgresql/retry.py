"""Retry an ENTIRE transaction callback only for chosen transient SQLSTATEs."""
import random
import time


def transaction_retry(attempt, max_attempts=3, wait=time.sleep, jitter=random.random):
    if max_attempts < 1:
        raise ValueError("max_attempts must include the first attempt")
    for number in range(max_attempts):
        try:
            return attempt()
        except Exception as error:
            if getattr(error, "sqlstate", None) not in {"40001", "40P01"} or number + 1 == max_attempts:
                raise
            wait(min(.01 * 2 ** number, .1) * jitter())
