from __future__ import annotations

from datetime import datetime, timezone
import time
from typing import Any, Callable

from .service import BatchQueueService


class NightlyBatchWorker:
    def __init__(
        self,
        *,
        queue_service: BatchQueueService,
        item_executor: Callable[[dict[str, Any], str, str], dict[str, Any]],
        policy: dict[str, Any],
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None:
        self.queue_service = queue_service
        self.item_executor = item_executor
        self.policy = policy
        self.monotonic = monotonic

    def run_once(self, queue_record_id: str, *, owner: str) -> dict[str, Any]:
        self.queue_service.acquire(queue_record_id, owner)
        started = self.monotonic()
        processed = 0
        max_items = int(self.policy["execution"]["maximum_items_per_cycle"])
        max_runtime = int(self.policy["execution"]["maximum_runtime_seconds"])

        while processed < max_items and self.monotonic() - started < max_runtime:
            item = self.queue_service.next_item(queue_record_id, owner)
            if item is None:
                break

            case_id = self._case_id(queue_record_id, item["item_id"])
            try:
                result = self.item_executor(
                    item,
                    case_id,
                    f"{queue_record_id}:{item['item_id']}",
                )
                self.queue_service.complete_item(
                    queue_record_id,
                    owner,
                    item["item_id"],
                    case_id=case_id,
                    result=result,
                )
            except Exception as exc:
                self.queue_service.fail_item(
                    queue_record_id,
                    owner,
                    item["item_id"],
                    case_id=case_id,
                    error={
                        "code": exc.__class__.__name__,
                        "message": str(exc),
                    },
                )
            processed += 1

        if processed >= max_items or self.monotonic() - started >= max_runtime:
            return self.queue_service.pause(
                queue_record_id,
                owner,
                "EXECUTION_BUDGET_REACHED",
            )
        return self.queue_service.finalize(queue_record_id, owner)

    def run_incomplete(self, *, owner_prefix: str = "nightly-worker") -> list[dict[str, Any]]:
        results = []
        for index, record in enumerate(self.queue_service.list_incomplete(), start=1):
            owner = f"{owner_prefix}-{index}"
            results.append(
                self.run_once(record["queue_record_id"], owner=owner)
            )
        return results

    @staticmethod
    def _case_id(queue_record_id: str, item_id: str) -> str:
        return f"QBCASE-{queue_record_id[-8:]}-{item_id}"
