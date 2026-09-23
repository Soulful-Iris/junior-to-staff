import math
from threading import Event, Thread
import unittest
from executor import Executor, Cancelled, Closed, DeadlineExceeded


class PublicationTests(unittest.TestCase):
    def held_after_last_check(self, pool, deadline=None):
        checked, release = Event(), Event()
        def work(ctx):
            original = ctx.check
            def final_check():
                original()
                checked.set()
                if not release.wait(2):
                    raise TimeoutError("test gate")
            ctx.check = final_check
            return "computed"
        task = pool.submit(work, deadline=deadline)
        self.assertTrue(checked.wait(2))
        return task, release

    def test_cancel_after_final_check_before_publication(self):
        pool = Executor(workers=1)
        task, release = self.held_after_last_check(pool)
        try:
            self.assertTrue(pool.cancel(task))
            release.set()
            with self.assertRaises(Cancelled):
                task.result(2)
            self.assertEqual((task.state, task.value, task.terminal_count), ("cancelled", None, 1))
            self.assertFalse(pool.cancel(task))
        finally:
            release.set()
            pool.shutdown(timeout=2)

    def test_deadline_rechecked_at_publication(self):
        now = [0.0]
        pool = Executor(workers=1, clock=lambda: now[0])
        task, release = self.held_after_last_check(pool, deadline=10)
        try:
            now[0] = 10
            release.set()
            with self.assertRaises(DeadlineExceeded):
                task.result(2)
            self.assertEqual(task.terminal_count, 1)
        finally:
            release.set()
            pool.shutdown(timeout=2)

    def test_invalid_deadlines_and_completed_immutability(self):
        pool = Executor(workers=1)
        try:
            for value in (math.nan, math.inf, -math.inf, True, "soon"):
                with self.subTest(value=value), self.assertRaises(ValueError):
                    pool.submit(lambda ctx: 1, deadline=value)
            with self.assertRaises(DeadlineExceeded):
                pool.submit(lambda ctx: 1, deadline=-1)
            task = pool.submit(lambda ctx: 7)
            self.assertEqual(task.result(2), 7)
            self.assertFalse(pool.cancel(task))
            self.assertEqual((task.state, task.value, task.terminal_count), ("succeeded", 7, 1))
            for timeout in (math.nan, math.inf, -1, True):
                with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                    task.result(timeout)
        finally:
            pool.shutdown(timeout=2)

    def test_huge_deadline_wait_is_capped_and_shutdown_wakes_it(self):
        pool = Executor(workers=1, capacity=1)
        entered, release, refused = Event(), Event(), Event()
        active = pool.submit(lambda ctx: (entered.set(), release.wait(2)))
        self.assertTrue(entered.wait(2))
        pool.submit(lambda ctx: 1)
        def producer():
            try:
                pool.submit(lambda ctx: 2, deadline=1e300)
            except Closed:
                refused.set()
        thread = Thread(target=producer)
        thread.start()
        try:
            with pool.cv:
                self.assertTrue(pool.cv.wait_for(lambda: pool.waiting_producers == 1, timeout=2))
            self.assertEqual(pool.snapshot()["waiting_producers"], 1)
            pool.shutdown(cancel_queued=True, wait=False)
            self.assertTrue(refused.wait(2))
        finally:
            release.set()
            thread.join(2)
            pool.shutdown(timeout=1e300)
        self.assertTrue(active.done.is_set())
