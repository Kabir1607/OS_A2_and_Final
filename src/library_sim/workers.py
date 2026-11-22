"""Real worker thread execution for concurrent resource operations.

Submits action batches across real operating-system threads, synchronizing
state mutations through the shared ResourceManager.
"""

from __future__ import annotations

import threading
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from time import perf_counter

from .models import Action, ActionType
from .resources import AcquireStatus, ResourceManager

_thread_id_counter = 0
_counter_lock = threading.Lock()


def _init_worker_thread() -> None:
    """Assign human-readable thread names matching [CONTRACT 3]."""
    global _thread_id_counter
    with _counter_lock:
        _thread_id_counter += 1
        threading.current_thread().name = f"worker-{_thread_id_counter}"


@dataclass(frozen=True)
class ActionBatch:
    """The actions ONE reader must perform at virtual time t.

    Runs sequentially within a batch, stopping at the first BLOCKED acquire.
    Different readers' batches run concurrently across worker threads.
    """
    reader_id: str
    t: int
    actions: tuple[Action, ...]


@dataclass(frozen=True)
class BatchResult:
    """Execution result of one ActionBatch."""
    reader_id: str
    done: int
    blocked: bool
    woken: tuple[str, ...]
    thread: str


class WorkerPool:
    """ThreadPool executor managing concurrent execution of ActionBatch items."""

    def __init__(self, manager: ResourceManager, num_workers: int = 2) -> None:
        self.manager = manager
        self.num_workers = max(1, num_workers)
        self._executor = ThreadPoolExecutor(
            max_workers=self.num_workers,
            initializer=_init_worker_thread,
        )
        self.recorded_overlaps: list[tuple[str, str]] = []

    def _execute_batch(self, batch: ActionBatch) -> tuple[BatchResult, float, float]:
        start = perf_counter()
        thread_name = threading.current_thread().name
        done = 0
        blocked = False
        woken_acc: list[str] = []

        for action in batch.actions:
            if action.action == ActionType.ACQUIRE:
                outcome = self.manager.acquire(batch.reader_id, action.resource_id, batch.t)
                if outcome.woken:
                    woken_acc.extend(outcome.woken)
                if outcome.status == AcquireStatus.GRANTED:
                    done += 1
                else:
                    blocked = True
                    break
            elif action.action == ActionType.RELEASE:
                rel_outcome = self.manager.release(batch.reader_id, action.resource_id, batch.t)
                if rel_outcome.woken:
                    woken_acc.extend(rel_outcome.woken)
                done += 1

        end = perf_counter()
        result = BatchResult(
            reader_id=batch.reader_id,
            done=done,
            blocked=blocked,
            woken=tuple(woken_acc),
            thread=thread_name,
        )
        return result, start, end

    def run_batches(self, batches: Sequence[ActionBatch]) -> list[BatchResult]:
        """Submit every batch to worker threads, returning results in input order.

        Re-raises any worker exceptions.
        """
        if not batches:
            return []

        futures = [self._executor.submit(self._execute_batch, b) for b in batches]
        results: list[BatchResult] = []
        intervals: list[tuple[str, float, float]] = []

        for future in futures:
            res, start, end = future.result()
            results.append(res)
            intervals.append((res.thread, start, end))

        # Check for real concurrency / execution overlap (S5b)
        for i in range(len(intervals)):
            for j in range(i + 1, len(intervals)):
                t1, s1, e1 = intervals[i]
                t2, s2, e2 = intervals[j]
                if t1 != t2 and not (e1 < s2 or e2 < s1):
                    self.recorded_overlaps.append((t1, t2))
                    if self.manager._tracer and self.manager._tracer.sink:
                        self.manager._tracer.sink.write(
                            f"[overlap] threads {t1} and {t2} overlapped in real execution\n"
                        )
                        self.manager._tracer.sink.flush()

        return results

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True)

    def __enter__(self) -> WorkerPool:
        return self

    def __exit__(self, *exc: object) -> None:
        self.shutdown()
