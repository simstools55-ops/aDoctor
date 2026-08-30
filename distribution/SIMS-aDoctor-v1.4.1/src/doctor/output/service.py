from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.doctor.events import MedicalRecordEventLog
from .result_builder import SingleCaseResultBuilder
from .writer_request_builder import WriterRequestBuilder


class OutputGenerationService:
    def __init__(
        self,
        event_log: MedicalRecordEventLog,
        result_builder: SingleCaseResultBuilder | None = None,
        writer_builder: WriterRequestBuilder | None = None,
    ) -> None:
        self.event_log = event_log
        self.result_builder = result_builder or SingleCaseResultBuilder()
        self.writer_builder = writer_builder or WriterRequestBuilder()

    def generate(self, medical_record: dict[str, Any], *, idempotency_key: str) -> dict[str, Any]:
        for event in medical_record.get("events", []):
            if (
                event.get("event_type") == "OUTPUT_GENERATED"
                and event.get("idempotency_key") == idempotency_key
            ):
                return event["payload"]["outputs"]

        result = self.result_builder.build(medical_record)
        writer_request = None
        referrals = medical_record.get("referrals", [])
        if referrals and referrals[-1].get("target") == "WRITER":
            writer_request = self.writer_builder.build(medical_record)

        outputs = {
            "single_case_result": result,
            "writer_request": writer_request,
        }
        now = datetime.now(timezone.utc)
        self.event_log.append(
            medical_record,
            event_type="OUTPUT_GENERATED",
            payload={"outputs": outputs},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("outputs", []).append(outputs)
        medical_record.setdefault("counters", {})["output_count"] = len(medical_record["outputs"])
        medical_record["updated_at"] = now.isoformat()
        return outputs
