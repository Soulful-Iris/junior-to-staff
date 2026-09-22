import subprocess
import sys
import unittest
from pathlib import Path
from threading import Barrier, Event, Thread
from executor import Executor, Closed, Cancelled, DeadlineExceeded, NestedSubmission


class Tests(unittest.TestCase):
    def test_bounds_outcomes_and_exception_permit_release(self):
        pool = Executor()
        entered, release = Barrier(5), Event()
        def held(ctx):
            entered.wait(timeout=2)
            release.wait(2)
            return 7
        active = [pool.submit(held) for _ in range(4)]
        entered.wait(timeout=2)
        queued = [pool.submit(lambda ctx: 11) for _ in range(8)]
        self.assertEqual(pool.snapshot()["queued"], 8)
        outcome = []
        producer = Thread(target=lambda: outcome.append(pool.submit(lambda ctx: 13)))
        producer.start()
        with pool.cv:
            self.assertTrue(pool.cv.wait_for(lambda: pool.waiting_producers == 1, timeout=2))
        release.set()
        producer.join(2)
        self.assertFalse(producer.is_alive())
        def bad(ctx):
            raise ValueError("task failure")
        failed = pool.submit(bad)
        good = pool.submit(lambda ctx: "slot released")
        pool.shutdown(timeout=3)
        all_tasks = active + queued + outcome + [failed, good]
        for task in all_tasks:
            self.assertTrue(task.done.is_set())
            self.assertEqual(task.terminal_count, 1)
        with self.assertRaises(ValueError):
            failed.result()
        self.assertEqual(good.result(), "slot released")
        state = pool.snapshot()
        self.assertEqual(state["peak_active"], 4)
        self.assertEqual(state["peak_queued"], 8)
        self.assertEqual(state["accepted"], state["completed"])
        self.assertEqual(state["active"], 0)

    def test_shutdown_wakes_blocked_producer_and_cancels_queued(self):
        pool = Executor(workers=1, capacity=1)
        entered, release, rejected = Event(), Event(), Event()
        def held(ctx):
            entered.set()
            release.wait(2)
            return "finished"
        running = pool.submit(held)
        self.assertTrue(entered.wait(2))
        queued = pool.submit(lambda ctx: "must not execute")
        def producer():
            try:
                pool.submit(lambda ctx: "refused")
            except Closed:
                rejected.set()
        thread = Thread(target=producer)
        thread.start()
        with pool.cv:
            self.assertTrue(pool.cv.wait_for(lambda: pool.waiting_producers == 1, timeout=2))
        pool.shutdown(cancel_queued=True, wait=False)
        self.assertTrue(rejected.wait(2))
        with self.assertRaises(Cancelled):
            queued.result(2)
        release.set()
        pool.shutdown(timeout=2)
        self.assertEqual(running.result(), "finished")
        thread.join(2)
        self.assertEqual(pool.snapshot()["accepted"], 2)

    def test_logical_deadlines_and_running_cancel(self):
        now = [0.0]
        pool = Executor(workers=1, capacity=1, clock=lambda: now[0])
        entered, release = Event(), Event()
        def held(ctx):
            entered.set()
            release.wait(2)
        running = pool.submit(held, deadline=10)
        self.assertTrue(entered.wait(2))
        queued = pool.submit(lambda ctx: self.fail("expired task ran"), deadline=3)
        refused = Event()
        def producer():
            try:
                pool.submit(lambda ctx: None, deadline=2)
            except DeadlineExceeded:
                refused.set()
        thread = Thread(target=producer)
        thread.start()
        with pool.cv:
            self.assertTrue(pool.cv.wait_for(lambda: pool.waiting_producers == 1, timeout=2))
        now[0] = 4
        pool.wake()
        self.assertTrue(refused.wait(2))
        pool.cancel(running)
        self.assertFalse(running.done.is_set())  # cancellation does not free a running resource
        release.set()
        pool.shutdown(timeout=2)
        with self.assertRaises(Cancelled):
            running.result()
        with self.assertRaises(DeadlineExceeded):
            queued.result()
        thread.join(2)

    def test_nested_submission_rejected_without_deadlock(self):
        pool = Executor()
        task = pool.submit(lambda ctx: pool.submit(lambda inner: 1).result())
        with self.assertRaises(NestedSubmission):
            task.result(2)
        joining = pool.submit(lambda ctx: pool.shutdown())
        with self.assertRaises(NestedSubmission):
            joining.result(2)
        pool.shutdown(timeout=2)

    def test_cancel_queued_releases_admission_and_finishes_once(self):
        pool = Executor(workers=1, capacity=1)
        entered, release = Event(), Event()
        pool.submit(lambda ctx: (entered.set(), release.wait(2)))
        self.assertTrue(entered.wait(2))
        doomed = pool.submit(lambda ctx: self.fail("cancelled callable ran"))
        self.assertTrue(pool.cancel(doomed))
        self.assertFalse(pool.cancel(doomed))
        replacement = pool.submit(lambda ctx: "reused queue slot")
        release.set()
        pool.shutdown(timeout=2)
        with self.assertRaises(Cancelled):
            doomed.result()
        self.assertEqual(doomed.terminal_count, 1)
        self.assertEqual(replacement.result(), "reused queue slot")
        self.assertEqual(pool.snapshot()["accepted"], pool.snapshot()["completed"])

    def test_shutdown_timeout_does_not_claim_running_task_stopped(self):
        pool = Executor(workers=1)
        entered, release = Event(), Event()
        task = pool.submit(lambda ctx: (entered.set(), release.wait(2)))
        self.assertTrue(entered.wait(2))
        with self.assertRaises(TimeoutError):
            pool.shutdown(timeout=0)
        self.assertFalse(task.done.is_set())
        release.set()
        pool.shutdown(timeout=2)

    def test_watchdog_detects_deliberate_nested_wait_deadlock(self):
        process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("deadlock_demo.py"))],
                                   stdout=subprocess.PIPE, text=True)
        try:
            # communicate has a watchdog; the deadlock itself is established by a Barrier.
            with self.assertRaises(subprocess.TimeoutExpired) as caught:
                process.communicate(timeout=1)
            output = caught.exception.output or b""
            if isinstance(output, bytes):
                output = output.decode()
            self.assertEqual(output.count("parent waiting for queued child"), 4)
        finally:
            process.kill()
            process.communicate(timeout=2)


if __name__ == "__main__":
    unittest.main()
