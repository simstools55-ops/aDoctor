from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
from typing import Any

from src.doctor.batch import BatchPriorityCalculator, BatchRequest
from .repository import BatchQueueRepository


class BatchQueueError(RuntimeError):
    pass


class BatchLockError(BatchQueueError):
    pass


def _queue_id(request_id: str) -> str:
    digest = hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:12].upper()
    return f"BQ-{digest}"


class BatchQueueService:
    def __init__(
        self,
        *,
        repository: BatchQueueRepository,
        policy: dict[str, Any],
        priority_calculator: BatchPriorityCalculator,
    ) -> None:
        self.repository = repository
        self.policy = policy
        self.priority_calculator = priority_calculator

    def enqueue(self, request: BatchRequest) -> dict[str, Any]:
        queue_record_id = _queue_id(request.batch_request_id)
        existing = self.repository.get(queue_record_id)
        if existing:
            return existing

        now = datetime.now(timezone.utc)
        items = []
        for item in request.items:
            items.append({
                "item_id": item.item_id,
                "article_id": item.article_id,
                "priority_score": self.priority_calculator.calculate(item),
                "status": "PENDING",
                "attempts": 0,
                "next_attempt_at": None,
                "case_id": None,
                "result": None,
                "error": None,
                "request_payload": item.request_payload,
                "url": item.url,
                "title": item.title,
            })
        items.sort(key=lambda row: -row["priority_score"])

        record = {
            "contract_name": "SIMS_DOCTOR_BATCH_QUEUE_RECORD_V1",
            "contract_version": "1.0",
            "queue_record_id": queue_record_id,
            "batch_request_id": request.batch_request_id,
            "site": request.site,
            "status": "QUEUED",
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "lock": None,
            "progress": self._progress(items),
            "items": items,
            "events": [
                self._event("BATCH_QUEUED", now, {"item_count": len(items)})
            ],
        }
        return self.repository.create(record)

    def acquire(self, queue_record_id: str, owner: str) -> dict[str, Any]:
        record = self._required(queue_record_id)
        now = datetime.now(timezone.utc)
        lock = record.get("lock")
        if lock and datetime.fromisoformat(lock["expires_at"]) > now and lock["owner"] != owner:
            raise BatchLockError(f"Queue is locked by {lock['owner']}")

        lease = int(self.policy["lock"]["lease_seconds"])
        record["lock"] = {
            "owner": owner,
            "acquired_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=lease)).isoformat(),
        }
        if record["status"] in {"QUEUED", "PAUSED"}:
            record["status"] = "RUNNING"
            record["events"].append(
                self._event("BATCH_STARTED", now, {"owner": owner})
            )
        record["updated_at"] = now.isoformat()
        return self.repository.save(record)

    def renew(self, queue_record_id: str, owner: str) -> dict[str, Any]:
        record = self._required(queue_record_id)
        self._assert_owner(record, owner)
        now = datetime.now(timezone.utc)
        lease = int(self.policy["lock"]["lease_seconds"])
        record["lock"]["expires_at"] = (
            now + timedelta(seconds=lease)
        ).isoformat()
        record["updated_at"] = now.isoformat()
        return self.repository.save(record)

    def release(self, queue_record_id: str, owner: str) -> dict[str, Any]:
        record = self._required(queue_record_id)
        self._assert_owner(record, owner)
        record["lock"] = None
        record["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self.repository.save(record)

    def next_item(self, queue_record_id: str, owner: str) -> dict[str, Any] | None:
        record = self._required(queue_record_id)
        self._assert_owner(record, owner)
        now = datetime.now(timezone.utc)

        candidates = [
            item for item in record["items"]
            if item["status"] in {"PENDING", "FAILED"}
            and (
                item["next_attempt_at"] is None
                or datetime.fromisoformat(item["next_attempt_at"]) <= now
            )
            and item["attempts"] < self.policy["retry"]["maximum_attempts_per_item"]
        ]
        if not candidates:
            return None
        candidates.sort(key=lambda row: -row["priority_score"])
        item = candidates[0]
        item["status"] = "RUNNING"
        item["attempts"] += 1
        item["error"] = None
        record["progress"] = self._progress(record["items"])
        record["updated_at"] = now.isoformat()
        self.repository.save(record)
        return dict(item)

    def complete_item(
        self,
        queue_record_id: str,
        owner: str,
        item_id: str,
        *,
        case_id: str,
        result: dict[str, Any],
    ) -> dict[str, Any]:
        record = self._required(queue_record_id)
        self._assert_owner(record, owner)
        item = self._item(record, item_id)
        item.update({
            "status": "COMPLETED",
            "case_id": case_id,
            "result": result,
            "error": None,
            "next_attempt_at": None,
        })
        self._checkpoint(record, "BATCH_PROGRESS_UPDATED", {"item_id": item_id})
        return self.repository.save(record)

    def fail_item(
        self,
        queue_record_id: str,
        owner: str,
        item_id: str,
        *,
        case_id: str | None,
        error: dict[str, Any],
    ) -> dict[str, Any]:
        record = self._required(queue_record_id)
        self._assert_owner(record, owner)
        item = self._item(record, item_id)
        attempts = item["attempts"]
        maximum = self.policy["retry"]["maximum_attempts_per_item"]
        if attempts >= maximum:
            next_attempt_at = None
        else:
            delays = self.policy["retry"]["backoff_seconds"]
            delay = delays[min(attempts - 1, len(delays) - 1)]
            next_attempt_at = (
                datetime.now(timezone.utc) + timedelta(seconds=delay)
            ).isoformat()
        item.update({
            "status": "FAILED",
            "case_id": case_id,
            "result": None,
            "error": error,
            "next_attempt_at": next_attempt_at,
        })
        self._checkpoint(record, "BATCH_PROGRESS_UPDATED", {"item_id": item_id})
        return self.repository.save(record)

    def pause(self, queue_record_id: str, owner: str, reason: str) -> dict[str, Any]:
        record = self._required(queue_record_id)
        self._assert_owner(record, owner)
        now = datetime.now(timezone.utc)
        for item in record["items"]:
            if item["status"] == "RUNNING":
                item["status"] = "PENDING"
        record["status"] = "PAUSED"
        record["lock"] = None
        record["progress"] = self._progress(record["items"])
        record["events"].append(
            self._event("BATCH_PAUSED", now, {"reason": reason})
        )
        record["updated_at"] = now.isoformat()
        return self.repository.save(record)

    def finalize(self, queue_record_id: str, owner: str) -> dict[str, Any]:
        record = self._required(queue_record_id)
        self._assert_owner(record, owner)
        now = datetime.now(timezone.utc)
        progress = self._progress(record["items"])
        retryable = any(
            item["status"] == "FAILED"
            and item["attempts"] < self.policy["retry"]["maximum_attempts_per_item"]
            for item in record["items"]
        )
        pending = progress["pending"] + progress["running"]

        if pending or retryable:
            record["status"] = "PAUSED"
            event_type = "BATCH_PAUSED"
        elif progress["completed"] == 0 and progress["failed"] > 0:
            record["status"] = "FAILED"
            event_type = "BATCH_FAILED"
        elif progress["failed"] > 0:
            record["status"] = "COMPLETED_WITH_ERRORS"
            event_type = "BATCH_COMPLETED"
        else:
            record["status"] = "COMPLETED"
            event_type = "BATCH_COMPLETED"

        record["progress"] = progress
        record["lock"] = None
        record["events"].append(
            self._event(event_type, now, {"progress": progress})
        )
        record["updated_at"] = now.isoformat()
        return self.repository.save(record)

    def list_incomplete(self) -> list[dict[str, Any]]:
        return self.repository.list_incomplete()

    def _checkpoint(self, record, event_type, payload):
        now = datetime.now(timezone.utc)
        record["progress"] = self._progress(record["items"])
        record["events"].append(self._event(event_type, now, payload))
        record["updated_at"] = now.isoformat()

    @staticmethod
    def _progress(items):
        return {
            "total": len(items),
            "completed": sum(item["status"] == "COMPLETED" for item in items),
            "failed": sum(item["status"] == "FAILED" for item in items),
            "pending": sum(item["status"] == "PENDING" for item in items),
            "running": sum(item["status"] == "RUNNING" for item in items),
            "skipped": sum(item["status"] == "SKIPPED" for item in items),
        }

    @staticmethod
    def _event(event_type, occurred_at, payload):
        return {
            "event_type": event_type,
            "occurred_at": occurred_at.isoformat(),
            "payload": payload,
        }

    def _required(self, queue_record_id):
        record = self.repository.get(queue_record_id)
        if record is None:
            raise BatchQueueError(f"Queue record not found: {queue_record_id}")
        return record

    @staticmethod
    def _item(record, item_id):
        for item in record["items"]:
            if item["item_id"] == item_id:
                return item
        raise BatchQueueError(f"Batch item not found: {item_id}")

    @staticmethod
    def _assert_owner(record, owner):
        lock = record.get("lock")
        if not lock or lock["owner"] != owner:
            raise BatchLockError("Worker does not own the queue lock")
        if datetime.fromisoformat(lock["expires_at"]) <= datetime.now(timezone.utc):
            raise BatchLockError("Queue lock has expired")
