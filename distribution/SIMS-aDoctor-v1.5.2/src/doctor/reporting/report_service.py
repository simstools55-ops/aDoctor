from __future__ import annotations

from datetime import datetime, timezone
import secrets

from src.doctor.events import MedicalRecordEventLog


class DoctorReportService:
    def __init__(self, *, generator, event_log: MedicalRecordEventLog):
        self.generator = generator
        self.event_log = event_log

    def generate(self, medical_record, *, audience, idempotency_key):
        for event in medical_record.get("events", []):
            report = event.get("payload", {}).get("doctor_report", {})
            if (
                event.get("event_type") == "DOCTOR_REPORT_GENERATED"
                and event.get("idempotency_key") == idempotency_key
                and report.get("audience") == audience
            ):
                return report

        if not medical_record.get("composite_diagnoses"):
            raise ValueError("Composite Diagnosis is required")
        if not medical_record.get("treatment_recommendations"):
            raise ValueError("Treatment Recommendation is required")

        now = datetime.now(timezone.utc)
        composite = medical_record["composite_diagnoses"][-1]
        recommendation = medical_record["treatment_recommendations"][-1]
        result = {
            "contract_name": "SIMS_DOCTOR_REPORT_V1",
            "contract_version": "1.0",
            "report_id": (
                f"RPT-{now.strftime('%Y%m%d-%H%M%S')}-"
                f"{secrets.token_hex(3).upper()}"
            ),
            "case_id": medical_record["case_id"],
            "medical_record_id": medical_record["medical_record_id"],
            "generated_at": now.isoformat(),
            **self.generator.generate(
                medical_record,
                composite,
                recommendation,
                audience=audience,
            ),
        }
        self.event_log.append(
            medical_record,
            event_type="DOCTOR_REPORT_GENERATED",
            payload={"doctor_report": result},
            occurred_at=now,
            idempotency_key=idempotency_key,
        )
        medical_record.setdefault("doctor_reports", []).append(result)
        medical_record.setdefault("counters", {})["doctor_report_count"] = len(
            medical_record["doctor_reports"]
        )
        medical_record["updated_at"] = now.isoformat()
        return result
