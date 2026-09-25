import queue
import threading

_SENTINEL = object()


def _check(workers, bound):
    if not isinstance(workers, int) or isinstance(workers, bool) or workers < 1:
        raise ValueError("workers must be a positive int")
    if not isinstance(bound, int) or isinstance(bound, bool) or bound < 1:
        raise ValueError("bound must be a positive int")


class WorkerPool:
    """N workers draining one bounded queue; errors are isolated; close() drains everything accepted."""

    def __init__(self, workers, bound, handler):
        _check(workers, bound)
        self.handler = handler
        self._jobs = queue.Queue(maxsize=bound)
        self._results = queue.Queue()
        self._closed = False
        self._lock = threading.Lock()
        self._threads = [threading.Thread(target=self._run, daemon=True) for _ in range(workers)]
        for t in self._threads:
            t.start()

    def _run(self):
        while True:
            job = self._jobs.get()
            if job is _SENTINEL:
                return
            try:
                self._results.put((job, ("ok", self.handler(job))))
            except Exception as exc:  # a bad job never stops a worker
                self._results.put((job, ("error", exc)))

    def submit(self, job):
        with self._lock:
            if self._closed:
                raise RuntimeError("pool is closed")
        self._jobs.put(job)  # blocks while the queue is full: backpressure

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
        for _ in self._threads:
            self._jobs.put(_SENTINEL)  # FIFO: sentinels follow every accepted job

    def join(self):
        for t in self._threads:
            t.join()

    def results(self):
        out = []
        while True:
            try:
                out.append(self._results.get_nowait())
            except queue.Empty:
                return out


class KeyedWorkerPool:
    """Jobs with equal keys go to the same worker and therefore never run concurrently."""

    def __init__(self, workers, bound, handler, key):
        _check(workers, bound)
        self.handler = handler
        self.key = key
        self._queues = [queue.Queue(maxsize=bound) for _ in range(workers)]
        self._results = queue.Queue()
        self._closed = False
        self._lock = threading.Lock()
        self._threads = [threading.Thread(target=self._run, args=(q,), daemon=True) for q in self._queues]
        for t in self._threads:
            t.start()

    def _run(self, q):
        while True:
            job = q.get()
            if job is _SENTINEL:
                return
            try:
                self._results.put((job, ("ok", self.handler(job))))
            except Exception as exc:
                self._results.put((job, ("error", exc)))

    def submit(self, job):
        with self._lock:
            if self._closed:
                raise RuntimeError("pool is closed")
        index = hash(self.key(job)) % len(self._queues)
        self._queues[index].put(job)

    def close(self):
        with self._lock:
            if self._closed:
                return
            self._closed = True
        for q in self._queues:
            q.put(_SENTINEL)

    def join(self):
        for t in self._threads:
            t.join()

    def results(self):
        out = []
        while True:
            try:
                out.append(self._results.get_nowait())
            except queue.Empty:
                return out
