from pathlib import Path
import json
from src.doctor.events import MedicalRecordEventLog
from src.doctor.reporting import DoctorReportGenerator, DoctorReportService

ROOT = Path(__file__).resolve().parents[2]

def test_report_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/reporting/medical_record.json").read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/reporting/doctor_report_policy_v1.json").read_text(encoding="utf-8")
    )
    service = DoctorReportService(
        generator=DoctorReportGenerator(policy),
        event_log=MedicalRecordEventLog({"DOCTOR_REPORT_GENERATED"}),
    )
    first = service.generate(record, audience="USER", idempotency_key="report:1")
    second = service.generate(record, audience="USER", idempotency_key="report:1")
    assert first["report_id"] == second["report_id"]
    assert len(record["doctor_reports"]) == 1
