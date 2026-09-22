"""A fixed worker pool with bounded admission; stdlib only, Python 3.10+."""
from collections import deque
from threading import Condition, Event, Thread, local
import time


class Closed(RuntimeError):
    pass


class NestedSubmission(RuntimeError):
    pass


class Cancelled(RuntimeError):
    pass


class DeadlineExceeded(TimeoutError):
    pass


class Context:
    def __init__(self, clock, deadline):
        self.clock, self.deadline, self.cancelled = clock, deadline, Event()

    def check(self):
        if self.cancelled.is_set():
            raise Cancelled("cooperative cancellation")
        if self.deadline is not None and self.clock() >= self.deadline:
            raise DeadlineExceeded("total task deadline")


class Task:
    def __init__(self, fn, context):
        self.fn, self.context = fn, context
        self.done = Event()
        self.state, self.value, self.error, self.terminal_count = "queued", None, None, 0

    def result(self, timeout=None):
        if not self.done.wait(timeout):
            raise TimeoutError("waiting did not cancel the task")
        if self.error is not None:
            raise self.error
        return self.value


class Executor:
    def __init__(self, workers=4, capacity=8, clock=time.monotonic):
        if workers <= 0 or capacity <= 0:
            raise ValueError("positive workers and queue capacity required")
        self.capacity, self.clock = capacity, clock
        self.cv, self.queue, self.worker_local = Condition(), deque(), local()
        self.closed, self.active = False, 0
        self.peak_active, self.peak_queued, self.accepted, self.completed = 0, 0, 0, 0
        self.waiting_producers = 0
        self.threads = [Thread(target=self._worker, name=f"executor-{i}", daemon=True) for i in range(workers)]
        for thread in self.threads:
            thread.start()

    def wake(self):
        """Notify predicate rechecks after an injected logical clock advances."""
        with self.cv:
            self.cv.notify_all()

    def submit(self, fn, *, deadline=None):
        if getattr(self.worker_local, "inside", False):
            raise NestedSubmission("workers cannot submit into their own pool")
        with self.cv:
            # Predicate: admission is possible OR shutdown/deadline requires refusal.
            while len(self.queue) >= self.capacity and not self.closed:
                remaining = None if deadline is None else deadline - self.clock()
                if remaining is not None and remaining <= 0:
                    raise DeadlineExceeded("admission deadline")
                self.waiting_producers += 1
                self.cv.notify_all()
                try:
                    self.cv.wait(remaining)
                finally:
                    self.waiting_producers -= 1
            if self.closed:
                raise Closed("executor closed")
            if deadline is not None and self.clock() >= deadline:
                raise DeadlineExceeded("admission deadline")
            task = Task(fn, Context(self.clock, deadline))
            self.queue.append(task)
            self.accepted += 1
            self.peak_queued = max(self.peak_queued, len(self.queue))
            self.cv.notify_all()
            return task

    def _finish(self, task, state, value=None, error=None):
        # Caller owns cv. Only internal state and Event are changed under this lock.
        assert not task.done.is_set()
        task.state, task.value, task.error = state, value, error
        task.terminal_count += 1
        self.completed += 1
        task.done.set()

    def cancel(self, task):
        with self.cv:
            if task.done.is_set():
                return False
            if task in self.queue:
                self.queue.remove(task)
                self._finish(task, "cancelled", error=Cancelled("cancelled before start"))
            else:
                task.context.cancelled.set()
            self.cv.notify_all()
            return True

    def _worker(self):
        self.worker_local.inside = True
        while True:
            with self.cv:
                # A notification is not a promise: always recheck this predicate.
                while not self.queue and not self.closed:
                    self.cv.wait()
                if not self.queue:
                    return
                task = self.queue.popleft()
                self.active += 1
                self.peak_active = max(self.peak_active, self.active)
                task.state = "running"
                self.cv.notify_all()  # free queue slot wakes a blocked producer
            state, value, error = "succeeded", None, None
            try:
                task.context.check()
                value = task.fn(task.context)  # never run arbitrary user code under cv
                task.context.check()
            except Cancelled as exc:
                state, error = "cancelled", exc
            except DeadlineExceeded as exc:
                state, error = "expired", exc
            except BaseException as exc:
                state, error = "failed", exc
            finally:
                with self.cv:
                    self.active -= 1  # release capacity even after failure
                    self._finish(task, state, value, error)
                    self.cv.notify_all()

    def shutdown(self, *, cancel_queued=False, wait=True, timeout=None):
        if wait and getattr(self.worker_local, "inside", False):
            raise NestedSubmission("worker cannot join its own executor")
        with self.cv:
            self.closed = True
            if cancel_queued:
                while self.queue:
                    task = self.queue.popleft()
                    self._finish(task, "cancelled", error=Cancelled("shutdown before start"))
            self.cv.notify_all()  # includes blocked producers and idle workers
        if wait:
            end = None if timeout is None else time.monotonic() + timeout
            for thread in self.threads:
                thread.join(None if end is None else max(0, end - time.monotonic()))
            if any(thread.is_alive() for thread in self.threads):
                raise TimeoutError("running work still owns resources")

    def snapshot(self):
        with self.cv:
            return dict(active=self.active, queued=len(self.queue), accepted=self.accepted,
                        completed=self.completed, peak_active=self.peak_active, peak_queued=self.peak_queued)
