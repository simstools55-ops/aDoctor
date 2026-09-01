from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import secrets
from typing import Any, Callable

from .models import BatchRequest, BatchItem
from .priority import BatchPriorityCalculator


class BatchDoctorError(RuntimeError):
    pass


def _batch_run_id(now: datetime) -> str:
    return f"BRUN-{now.strftime('%Y%m%d-%H%M%S')}-{secrets.token_hex(3).upper()}"


class BatchDoctorRunner:
    def __init__(
        self,
        *,
        policy: dict[str, Any],
        priority_calculator: BatchPriorityCalculator,
        single_case_executor: Callable[[BatchItem, str, str], dict[str, Any]],
    ) -> None:
        self.policy = policy
        self.priority_calculator = priority_calculator
        self.single_case_executor = single_case_executor

    def run(
        self,
        request: BatchRequest,
        *,
        previous_result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        maximum = self.policy["limits"]["maximum_batch_size"]
        if len(request.items) > maximum:
            raise BatchDoctorError(
                f"Batch size {len(request.items)} exceeds maximum {maximum}"
            )

        started = datetime.now(timezone.utc)
        run_id = _batch_run_id(started)
        prior_by_item = {
            item["item_id"]: item
            for item in (previous_result or {}).get("items", [])
        }

        prioritized = [
            (index, item, self.priority_calculator.calculate(item))
            for index, item in enumerate(request.items)
        ]
        prioritized.sort(key=lambda row: (-row[2], row[0]))

        results = []
        global_errors = []

        for _, item, priority_score in prioritized:
            prior = prior_by_item.get(item.item_id)
            if prior and prior.get("status") == "COMPLETED":
                results.append({
                    **prior,
                    "status": "SKIPPED",
                    "priority_score": priority_score,
                    "error": None,
                })
                continue

            attempts = int(prior.get("attempts", 0)) if prior else 0
            maximum_attempts = self.policy["limits"]["maximum_attempts_per_case"]
            if attempts >= maximum_attempts:
                results.append({
                    "item_id": item.item_id,
                    "article_id": item.article_id,
                    "priority_score": priority_score,
                    "status": "FAILED",
                    "attempts": attempts,
                    "case_id": prior.get("case_id") if prior else None,
                    "result": None,
                    "error": {
                        "code": "MAXIMUM_ATTEMPTS_REACHED",
                        "message": "The case reached the maximum retry count.",
                    },
                })
                continue

            case_id = self._case_id(request, item)
            attempts += 1
            try:
                result = self.single_case_executor(
                    item,
                    case_id,
                    f"{request.batch_request_id}:{item.item_id}",
                )
                results.append({
                    "item_id": item.item_id,
                    "article_id": item.article_id,
                    "priority_score": priority_score,
                    "status": "COMPLETED",
                    "attempts": attempts,
                    "case_id": case_id,
                    "result": result,
                    "error": None,
                })
            except Exception as exc:
                error = {
                    "code": exc.__class__.__name__,
                    "message": str(exc),
                }
                results.append({
                    "item_id": item.item_id,
                    "article_id": item.article_id,
                    "priority_score": priority_score,
                    "status": "FAILED",
                    "attempts": attempts,
                    "case_id": case_id,
                    "result": None,
                    "error": error,
                })
                global_errors.append({
                    "item_id": item.item_id,
                    **error,
                })

        completed = datetime.now(timezone.utc)
        summary = self._summary(results)
        if summary["completed"] == 0 and summary["failed"] > 0:
            status = "FAILED"
        elif summary["failed"] > 0:
            status = "COMPLETED_WITH_ERRORS"
        else:
            status = "COMPLETED"

        return {
            "contract_name": "SIMS_DOCTOR_BATCH_RESULT_V1",
            "contract_version": "1.0",
            "batch_run_id": run_id,
            "batch_request_id": request.batch_request_id,
            "status": status,
            "started_at": started.isoformat(),
            "completed_at": completed.isoformat(),
            "summary": summary,
            "items": results,
            "errors": global_errors,
        }

    @staticmethod
    def _case_id(request: BatchRequest, item: BatchItem) -> str:
        digest = hashlib.sha256(
            json.dumps(
                {
                    "batch_request_id": request.batch_request_id,
                    "item_id": item.item_id,
                    "article_id": item.article_id,
                },
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()[:8].upper()
        return f"BCASE-{digest}"

    @staticmethod
    def _summary(items: list[dict[str, Any]]) -> dict[str, int]:
        summary = {
            "total": len(items),
            "completed": 0,
            "failed": 0,
            "skipped": 0,
            "writer_referrals": 0,
            "creator_referrals": 0,
            "merge_referrals": 0,
            "follow_up": 0,
        }
        for item in items:
            status = item["status"]
            if status == "COMPLETED":
                summary["completed"] += 1
            elif status == "FAILED":
                summary["failed"] += 1
            elif status == "SKIPPED":
                summary["skipped"] += 1

            result = item.get("result") or {}
            referral = result.get("referral") or {}
            target = referral.get("target")
            if target == "WRITER":
                summary["writer_referrals"] += 1
            elif target == "CREATOR":
                summary["creator_referrals"] += 1
            elif target == "MERGE":
                summary["merge_referrals"] += 1
            if result.get("result_status") == "FOLLOW_UP":
                summary["follow_up"] += 1
        return summary
