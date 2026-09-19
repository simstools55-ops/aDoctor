from __future__ import annotations

from typing import Any, Dict

from doctor.common.clock import Clock, SystemClock, isoformat_seconds
from doctor.common.errors import DoctorError, INTERNAL_ERROR
from doctor.common.id_generator import generate_case_id, generate_request_id, medical_record_id
from doctor.medical_record.medical_record_generator import append_request, create_medical_record
from doctor.medical_record.medical_record_repository import InMemoryMedicalRecordRepository
from doctor.receiver.request_receiver import receive_request
from doctor.registry.case_registry import InMemoryCaseRegistry
from doctor.result.result_generator import error_result, success_result


class DoctorReceptionService:
    def __init__(
        self,
        registry: InMemoryCaseRegistry | None = None,
        records: InMemoryMedicalRecordRepository | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.registry = registry or InMemoryCaseRegistry()
        self.records = records or InMemoryMedicalRecordRepository()
        self.clock = clock or SystemClock()

    def accept(self, payload: Any) -> Dict[str, Any]:
        now = self.clock.now()
        completed_at = isoformat_seconds(now)
        try:
            received = receive_request(payload)
            request = received.normalized_request
            request_id = generate_request_id(now)
            site_id = request["site"]["site_id"]
            article_id = request["article"]["article_id"]

            existing = self.registry.find_active(site_id, article_id)
            if existing:
                record_id = existing["medical_record_id"]
                record = self.records.get(record_id)
                if record is None:
                    raise DoctorError(INTERNAL_ERROR, "active case has no medical record")
                updated_record = append_request(record, request, request_id, completed_at)
                updated_case = dict(existing)
                updated_case["latest_request_id"] = request_id
                updated_case["updated_at"] = completed_at
                # Commit as one logical transaction. Roll back the record if registry fails.
                self.records.save(updated_record)
                try:
                    self.registry.save(updated_case)
                except Exception:
                    self.records.save(record)
                    raise
                return success_result(
                    "EXISTING_CASE_REUSED", completed_at, request_id,
                    existing["case_id"], record_id, updated_record["case_status"],
                )

            case_id = request.get("case_id") or generate_case_id(now, self.registry)
            record_id = medical_record_id(case_id)
            case = {
                "case_id": case_id,
                "site_id": site_id,
                "article_id": article_id,
                "article_url": request["article"]["url"],
                "case_status": "READY_FOR_OBSERVATION",
                "created_at": completed_at,
                "updated_at": completed_at,
                "latest_request_id": request_id,
                "medical_record_id": record_id,
                "diagnosis_count": 0,
                "referral_count": 0,
                "follow_up_count": 0,
            }
            record = create_medical_record(request, request_id, case_id, record_id, completed_at)

            self.registry.save(case)
            try:
                self.records.save(record)
            except Exception:
                self.registry.delete(case_id)
                raise

            return success_result(
                "ACCEPTED", completed_at, request_id, case_id,
                record_id, "READY_FOR_OBSERVATION",
            )
        except DoctorError as error:
            return error_result(error, completed_at)
        except Exception:
            return error_result(DoctorError(INTERNAL_ERROR, "internal reception error"), completed_at)
