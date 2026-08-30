import json
from pathlib import Path

from doctor.medical_record.medical_record_generator import append_request, create_medical_record

ROOT = Path(__file__).resolve().parents[2]


def request():
    return json.loads((ROOT / "tests/fixtures/valid/single_case_request.json").read_text(encoding="utf-8"))


def test_initial_record_has_zero_clinical_counters():
    record = create_medical_record(
        request(), "DREQ-1", "CASE-20260804-000001", "MR-CASE-20260804-000001",
        "2026-08-04T10:00:00+00:00",
    )
    assert record["case_status"] == "READY_FOR_OBSERVATION"
    assert record["counters"]["request_count"] == 1
    assert record["counters"]["diagnosis_count"] == 0
    assert record["observations"] == []


def test_append_request_preserves_original_record():
    record = create_medical_record(
        request(), "DREQ-1", "CASE-20260804-000001", "MR-CASE-20260804-000001",
        "2026-08-04T10:00:00+00:00",
    )
    updated = append_request(record, request(), "DREQ-2", "2026-08-04T11:00:00+00:00")
    assert record["counters"]["request_count"] == 1
    assert updated["counters"]["request_count"] == 2
    assert len(updated["requests"]) == 2
