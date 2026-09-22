"""Deliberately wrong: run only in the subprocess watchdog test."""
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

pool = ThreadPoolExecutor(max_workers=4)
barrier = Barrier(4)


def parent():
    barrier.wait()
    child = pool.submit(lambda: "child")
    print("parent waiting for queued child", flush=True)
    return child.result()  # all workers wait; no worker can run any child


parents = [pool.submit(parent) for _ in range(4)]
for future in parents:
    future.result()
