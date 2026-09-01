from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from src.doctor.batch import BatchRequest
from src.doctor.batch.queue import BatchQueueService


class SbmIntegrationError(ValueError):
    pass


class SbmBatchGateway:
    TERMINAL = {"COMPLETED", "COMPLETED_WITH_ERRORS", "FAILED", "CANCELLED"}

    def __init__(self, queue_service: BatchQueueService) -> None:
        self.queue_service = queue_service

    def submit(self, payload: dict[str, Any]) -> dict[str, Any]:
        self._validate_submission(payload)
        batch_request = self._to_batch_request(payload)
        expected_queue_id = self._queue_id(payload["batch_request_id"])
        duplicate = self.queue_service.repository.get(expected_queue_id) is not None
        record = self.queue_service.enqueue(batch_request)
        return {
            "contract_name": "SIMS_SBM_DOCTOR_BATCH_ACCEPTED_V1",
            "contract_version": "1.0",
            "batch_request_id": payload["batch_request_id"],
            "queue_record_id": record["queue_record_id"],
            "status": "ACCEPTED",
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "item_count": len(payload["items"]),
            "duplicate_submission": duplicate,
        }

    def status(self, queue_record_id: str) -> dict[str, Any]:
        record = self.queue_service.repository.get(queue_record_id)
        if record is None:
            raise SbmIntegrationError(f"Queue record not found: {queue_record_id}")
        return {
            "contract_name": "SIMS_SBM_DOCTOR_BATCH_STATUS_V1",
            "contract_version": "1.0",
            "batch_request_id": record["batch_request_id"],
            "queue_record_id": record["queue_record_id"],
            "status": record["status"],
            "progress": record["progress"],
            "items": [
                {
                    "item_id": item["item_id"],
                    "article_id": item["article_id"],
                    "status": item["status"],
                    "attempts": item["attempts"],
                    "case_id": item.get("case_id"),
                    "error_code": (
                        item.get("error", {}).get("code")
                        if item.get("error") else None
                    ),
                }
                for item in record["items"]
            ],
            "updated_at": record["updated_at"],
            "result_ready": record["status"] in self.TERMINAL,
        }

    def export_result(self, queue_record_id: str) -> dict[str, Any]:
        record = self.queue_service.repository.get(queue_record_id)
        if record is None:
            raise SbmIntegrationError(f"Queue record not found: {queue_record_id}")
        if record["status"] not in self.TERMINAL:
            raise SbmIntegrationError("Batch result is not ready")

        items = []
        for item in record["items"]:
            raw = item.get("result") or {}
            single_case_result = raw.get("single_case_result")
            writer_request = raw.get("writer_request")
            if single_case_result is None and raw.get("contract_name") == "SIMS_DOCTOR_SINGLE_CASE_RESULT_V1":
                single_case_result = raw
            items.append({
                "item_id": item["item_id"],
                "article_id": item["article_id"],
                "status": item["status"],
                "case_id": item.get("case_id"),
                "single_case_result": single_case_result,
                "writer_request": writer_request,
                "error": item.get("error"),
            })

        summary = {
            "total": len(items),
            "completed": sum(x["status"] == "COMPLETED" for x in items),
            "failed": sum(x["status"] == "FAILED" for x in items),
            "writer_requests": sum(x["writer_request"] is not None for x in items),
            "follow_up": sum(
                (x["single_case_result"] or {}).get("result_status") == "FOLLOW_UP"
                for x in items
            ),
        }
        canonical = {
            "batch_request_id": record["batch_request_id"],
            "queue_record_id": record["queue_record_id"],
            "site_id": record["site"]["site_id"],
            "batch_status": record["status"],
            "summary": summary,
            "items": items,
        }
        fingerprint = hashlib.sha256(
            json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            .encode("utf-8")
        ).hexdigest()
        return {
            "contract_name": "SIMS_SBM_DOCTOR_BATCH_RESULT_PACKAGE_V1",
            "contract_version": "1.0",
            "package_id": f"SBMR-{fingerprint[:16].upper()}",
            **canonical,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "result_fingerprint": fingerprint,
        }

    @staticmethod
    def _to_batch_request(payload: dict[str, Any]) -> BatchRequest:
        return BatchRequest.from_dict({
            "batch_request_id": payload["batch_request_id"],
            "requested_at": payload["requested_at"],
            "site": payload["site"],
            "items": [
                {
                    "item_id": item["item_id"],
                    "article_id": item["article_id"],
                    "url": item["url"],
                    "title": item["title"],
                    "request_payload": item["single_case_request"],
                    "longitudinal_profile": item.get("longitudinal_profile"),
                    "current_metrics": item.get("current_metrics"),
                }
                for item in payload["items"]
            ],
        })

    @staticmethod
    def _validate_submission(payload: dict[str, Any]) -> None:
        if payload.get("contract_name") != "SIMS_SBM_DOCTOR_BATCH_REQUEST_V1":
            raise SbmIntegrationError("Unsupported SBM batch contract")
        if payload.get("contract_version") != "1.0":
            raise SbmIntegrationError("Unsupported SBM batch contract version")
        article_ids = [item["article_id"] for item in payload.get("items", [])]
        if not article_ids:
            raise SbmIntegrationError("Batch contains no articles")
        if len(article_ids) != len(set(article_ids)):
            raise SbmIntegrationError("Duplicate article ID in SBM batch")

    @staticmethod
    def _queue_id(request_id: str) -> str:
        digest = hashlib.sha256(request_id.encode("utf-8")).hexdigest()[:12].upper()
        return f"BQ-{digest}"
