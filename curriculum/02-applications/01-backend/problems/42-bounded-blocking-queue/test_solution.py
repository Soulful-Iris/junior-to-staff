from collections import Counter
from queue import Queue
import threading
import unittest
from unittest.mock import patch
from solution import BoundedBlockingQueue, QueueClosed


class ObservedCondition(threading.Condition):
    """Signals entry to wait while still owning its mutex; no scheduling sleeps."""
    def __init__(self):
        super().__init__()
        self.waiting = threading.Event()

    def wait(self, timeout=None):
        self.waiting.set()
        return super().wait(timeout)


class Tests(unittest.TestCase):
    def start_operation(self, operation):
        outcome = Queue()
        def run():
            try:
                outcome.put(('value', operation()))
            except Exception as error:
                outcome.put(('error', error))
        worker = threading.Thread(target=run, daemon=True)
        worker.start()
        return worker, outcome

    def finish(self, worker, outcome):
        worker.join(2)
        self.assertFalse(worker.is_alive(), 'operation failed to terminate')
        return outcome.get_nowait()

    def test_blocked_producer_spurious_wakeup_and_shutdown(self):
        condition = ObservedCondition()
        queue = BoundedBlockingQueue(1, condition=condition)
        queue.put('first')
        worker, outcome = self.start_operation(lambda: queue.put('second'))
        try:
            self.assertTrue(condition.waiting.wait(2))
            with condition:
                condition.waiting.clear()
                condition.notify_all()  # Capacity still full: producer must wait again.
            self.assertTrue(condition.waiting.wait(2))
            self.assertTrue(outcome.empty())
        finally:
            queue.shutdown()
        kind, error = self.finish(worker, outcome)
        self.assertEqual(kind, 'error')
        self.assertIsInstance(error, QueueClosed)
        self.assertEqual(queue.get(timeout=0), 'first')
        with self.assertRaises(QueueClosed):
            queue.get(timeout=0)

    def test_blocked_producer_resumes_when_slot_freed(self):
        condition = ObservedCondition()
        queue = BoundedBlockingQueue(1, condition=condition)
        queue.put(1)
        worker, outcome = self.start_operation(lambda: queue.put(2))
        try:
            self.assertTrue(condition.waiting.wait(2))
            self.assertEqual(queue.get(timeout=0), 1)
            self.assertEqual(self.finish(worker, outcome), ('value', None))
            self.assertEqual(queue.get(timeout=0), 2)
        finally:
            queue.shutdown()

    def test_waiting_consumer_cancel_and_close(self):
        condition = ObservedCondition()
        queue = BoundedBlockingQueue(2, condition=condition)
        worker, outcome = self.start_operation(queue.get)
        try:
            self.assertTrue(condition.waiting.wait(2))
        finally:
            queue.shutdown(cancel_pending=True)
        kind, error = self.finish(worker, outcome)
        self.assertEqual(kind, 'error')
        self.assertIsInstance(error, QueueClosed)
        queue = BoundedBlockingQueue(2)
        queue.put('a')
        queue.put('b')
        self.assertEqual(queue.shutdown(cancel_pending=True), ['a', 'b'])
        self.assertEqual(queue.shutdown(), [])
        with self.assertRaises(QueueClosed):
            queue.put('c')
        with self.assertRaises(QueueClosed):
            queue.get(timeout=0)

    def test_competing_threads_no_loss_or_duplication(self):
        queue = BoundedBlockingQueue(3)
        start = threading.Barrier(5)
        results, errors = Queue(), Queue()
        def producer(identity):
            try:
                start.wait(2)
                for number in range(30):
                    queue.put((identity, number), timeout=2)
            except Exception as error:
                errors.put(error)
        def consumer():
            try:
                start.wait(2)
                while True:
                    try:
                        results.put(queue.get(timeout=2))
                    except QueueClosed:
                        return
            except Exception as error:
                errors.put(error)
        producers = [threading.Thread(target=producer, args=(i,), daemon=True) for i in range(2)]
        consumers = [threading.Thread(target=consumer, daemon=True) for _ in range(2)]
        for worker in producers + consumers:
            worker.start()
        try:
            start.wait(2)
            for worker in producers:
                worker.join(3)
                self.assertFalse(worker.is_alive())
        finally:
            queue.shutdown()
        for worker in consumers:
            worker.join(3)
            self.assertFalse(worker.is_alive())
        self.assertTrue(errors.empty(), list(errors.queue))
        actual = [results.get_nowait() for _ in range(results.qsize())]
        self.assertEqual(Counter(actual), Counter((i, n) for i in range(2) for n in range(30)))

    def test_timeout_zero_fifo_and_validation(self):
        queue = BoundedBlockingQueue(2)
        with self.assertRaises(TimeoutError):
            queue.get(timeout=0)
        queue.put(1, timeout=0)
        queue.put(2, timeout=0)
        with self.assertRaises(TimeoutError):
            queue.put(3, timeout=0)
        self.assertEqual([queue.get(timeout=0), queue.get(timeout=0)], [1, 2])
        with self.assertRaises(ValueError):
            queue.get(timeout=-1)
        with self.assertRaises(ValueError):
            BoundedBlockingQueue(0)

    def test_deadline_budget_survives_multiple_wakeups(self):
        class ScriptedCondition:
            def __init__(self):
                self.now, self.waits = 0, []
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def wait(self, timeout):
                self.waits.append(timeout)
                self.now += 2 if len(self.waits) == 1 else 3
        condition = ScriptedCondition()
        queue = BoundedBlockingQueue(1, condition=condition)
        with patch('solution.time.monotonic', side_effect=lambda: condition.now):
            with self.assertRaises(TimeoutError):
                queue.get(timeout=5)
        self.assertEqual(condition.waits, [5, 3])


if __name__ == '__main__':
    unittest.main()
