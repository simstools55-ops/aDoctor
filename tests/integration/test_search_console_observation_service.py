from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.search_console import SearchConsoleObservationInput, SearchConsoleObservationService


ROOT = Path(__file__).resolve().parents[2]


def medical_record():
    return {
        "contract_name": "SIMS_DOCTOR_MEDICAL_RECORD_V1",
        "contract_version": "1.0",
        "medical_record_id": "MR-CASE-20260804-000001",
        "case_id": "CASE-20260804-000001",
        "case_status": "READY_FOR_OBSERVATION",
        "patient": {
            "site_id": "sample-site",
            "site_name": "サンプルブログ",
            "blog_url": "https://example.invalid/",
            "article_id": "A000001",
            "article_url": "https://example.invalid/entry/example",
            "article_title": "テスト記事",
        },
        "requests": [],
        "events": [],
        "observations": [],
        "diagnoses": [],
        "referrals": [],
        "follow_ups": [],
        "counters": {
            "request_count": 1,
            "observation_count": 0,
            "diagnosis_count": 0,
            "referral_count": 0,
            "follow_up_count": 0,
        },
        "previous_case": None,
        "created_at": "2026-08-04T10:00:00+00:00",
        "updated_at": "2026-08-04T10:00:00+00:00",
    }


def input_data():
    data = json.loads(
        (ROOT / "tests/fixtures/search_console/complete_365_days.json").read_text(encoding="utf-8")
    )
    return SearchConsoleObservationInput.from_dict(data)


def test_records_observation_event_and_updates_counter():
    record = medical_record()
    log = MedicalRecordEventLog({"OBSERVATION_RECORDED"})
    service = SearchConsoleObservationService(log)
    result = service.record(record, input_data(), idempotency_key="gsc:CASE-20260804-000001:2026-08-04")

    assert result["observation_type"] == "SEARCH_CONSOLE"
    assert len(record["observations"]) == 1
    assert len(record["events"]) == 1
    assert record["counters"]["observation_count"] == 1
    assert record["case_status"] == "OBSERVING"


def test_replay_is_idempotent():
    record = medical_record()
    log = MedicalRecordEventLog({"OBSERVATION_RECORDED"})
    service = SearchConsoleObservationService(log)
    key = "gsc:CASE-20260804-000001:2026-08-04"
    first = service.record(record, input_data(), idempotency_key=key)
    second = service.record(record, input_data(), idempotency_key=key)

    assert first["observation_id"] == second["observation_id"]
    assert len(record["observations"]) == 1
    assert len(record["events"]) == 1
