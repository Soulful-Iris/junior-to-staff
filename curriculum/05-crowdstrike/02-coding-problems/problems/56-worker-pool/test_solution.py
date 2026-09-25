import threading
import time
import unittest
from collections import defaultdict
from solution import WorkerPool, KeyedWorkerPool


class WorkerPoolTests(unittest.TestCase):
    def test_parallel_processing(self):
        pool = WorkerPool(3, 4, lambda x: x * x)
        for i in range(10):
            pool.submit(i)
        pool.close()
        pool.join()
        results = pool.results()
        self.assertEqual(len(results), 10)
        self.assertEqual({outcome[1] for _, outcome in results}, {i * i for i in range(10)})
        self.assertTrue(all(outcome[0] == "ok" for _, outcome in results))

    def test_backpressure_blocks_submit(self):
        release = threading.Event()
        pool = WorkerPool(1, 2, lambda x: release.wait(5))
        pool.submit("a")           # taken by the worker, which now waits
        time.sleep(0.05)
        pool.submit("b")           # queue slot 1
        pool.submit("c")           # queue slot 2: queue is now full
        blocked = threading.Thread(target=pool.submit, args=("d",), daemon=True)
        blocked.start()
        blocked.join(0.2)
        self.assertTrue(blocked.is_alive(), "fourth submit should block while the queue is full")
        release.set()
        blocked.join(2)
        self.assertFalse(blocked.is_alive())
        pool.close()
        pool.join()
        self.assertEqual(len(pool.results()), 4)

    def test_error_isolation_and_drain(self):
        def handler(x):
            if x == 3:
                raise ValueError("bad job")
            return x

        pool = WorkerPool(2, 2, handler)
        for i in range(5):
            pool.submit(i)
        pool.close()
        pool.join()
        results = dict(pool.results())
        self.assertEqual(len(results), 5)
        self.assertEqual(results[3][0], "error")
        self.assertIsInstance(results[3][1], ValueError)
        self.assertEqual({k for k, v in results.items() if v[0] == "ok"}, {0, 1, 2, 4})

    def test_submit_after_close(self):
        pool = WorkerPool(1, 1, lambda x: x)
        pool.close()
        with self.assertRaises(RuntimeError):
            pool.submit(1)
        pool.join()

    def test_invalid(self):
        with self.assertRaises(ValueError):
            WorkerPool(0, 1, lambda x: x)
        with self.assertRaises(ValueError):
            KeyedWorkerPool(2, 0, lambda x: x, key=lambda x: x)

    def test_keyed_pool_serializes_equal_keys(self):
        active = defaultdict(int)
        peak = defaultdict(int)
        lock = threading.Lock()

        def handler(job):
            key = job[0]
            with lock:
                active[key] += 1
                peak[key] = max(peak[key], active[key])
            time.sleep(0.005)
            with lock:
                active[key] -= 1
            return job

        pool = KeyedWorkerPool(4, 8, handler, key=lambda job: job[0])
        for i in range(20):
            pool.submit(("k1" if i % 2 else "k2", i))
        pool.close()
        pool.join()
        self.assertEqual(len(pool.results()), 20)
        self.assertEqual(max(peak.values()), 1)


if __name__ == "__main__":
    unittest.main()
