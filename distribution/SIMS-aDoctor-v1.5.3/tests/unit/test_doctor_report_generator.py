from pathlib import Path
import json
from src.doctor.reporting import DoctorReportGenerator

ROOT = Path(__file__).resolve().parents[2]

def load():
    return json.loads(
        (ROOT / "tests/fixtures/reporting/medical_record.json").read_text(encoding="utf-8")
    )

def policy():
    return json.loads(
        (ROOT / "knowledge/reporting/doctor_report_policy_v1.json").read_text(encoding="utf-8")
    )

def test_user_report_hides_internal_trace():
    record = load()
    report = DoctorReportGenerator(policy()).generate(
        record,
        record["composite_diagnoses"][-1],
        record["treatment_recommendations"][-1],
        audience="USER",
    )
    assert report["diagnosis"]["label"] == "局所改善"
    assert "referral_request" not in report["trace"]

def test_system_report_contains_trace():
    record = load()
    report = DoctorReportGenerator(policy()).generate(
        record,
        record["composite_diagnoses"][-1],
        record["treatment_recommendations"][-1],
        audience="SYSTEM",
    )
    assert "supporting_assessments" in report["trace"]
    assert "referral_request" in report["trace"]
