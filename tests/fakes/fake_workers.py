"""Shared fake for WorkerPool (S6c).

Synchronous in-process worker stand-in matching library_sim.workers signatures.
"""

from __future__ import annotations

import threading
from collections.abc import Sequence
from dataclasses import dataclass

from library_sim.models import Action, ActionType
from library_sim.resources import AcquireStatus, ResourceManager


@dataclass(frozen=True)
class ActionBatch:
    reader_id: str
    t: int
    actions: tuple[Action, ...]


@dataclass(frozen=True)
class BatchResult:
    reader_id: str
    done: int
    blocked: bool
    woken: tuple[str, ...]
    thread: str


class WorkerPool:
    """Minimal fake worker pool executing batches synchronously."""

    def __init__(self, manager: ResourceManager, num_workers: int = 2) -> None:
        self.manager = manager
        self.num_workers = num_workers

    def run_batches(self, batches: Sequence[ActionBatch]) -> list[BatchResult]:
        results: list[BatchResult] = []
        thread_name = threading.current_thread().name

        for batch in batches:
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

            results.append(
                BatchResult(
                    reader_id=batch.reader_id,
                    done=done,
                    blocked=blocked,
                    woken=tuple(woken_acc),
                    thread=thread_name,
                )
            )

        return results

    def shutdown(self) -> None:
        pass

    def __enter__(self) -> WorkerPool:
        return self

    def __exit__(self, *exc: object) -> None:
        pass
