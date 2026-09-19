from pathlib import Path

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.vital_signs import VitalSignsEngine


ROOT = Path(__file__).resolve().parents[2]


def make_record():
    return {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "events": [],
        "observations": [
            {
                "observation_id": "OBS-20260804-120000-ABCDEF",
                "observation_type": "SEARCH_CONSOLE",
                "observed_at": "2026-08-04T12:00:00+00:00",
                "source": "GOOGLE_SEARCH_CONSOLE",
                "schema_version": "1.0",
                "facts": {
                    "periods": {
                        "days_28": {"clicks": 5, "impressions": 1000, "ctr": 0.005, "position": 8.0},
                        "days_90": {"clicks": 40, "impressions": 5000, "ctr": 0.008, "position": 7.0},
                        "days_365": {"clicks": 100, "impressions": 15000, "ctr": 0.0067, "position": 8.5}
                    },
                    "queries": [],
                    "retrieval": {}
                }
            },
            {
                "observation_id": "OBS-20260804-120100-ABCDEF",
                "observation_type": "METADATA",
                "observed_at": "2026-08-04T12:01:00+00:00",
                "source": "ARTICLE",
                "schema_version": "1.0",
                "facts": {"last_modified_at": "2026-06-01T00:00:00+00:00"}
            }
        ],
        "evidence": [],
        "vital_profiles": [],
        "counters": {"vital_profile_count": 0},
        "updated_at": "2026-08-04T12:00:00+00:00"
    }


def engine():
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    return VitalSignsEngine(ckb, MedicalRecordEventLog({"VITAL_SIGNS_CALCULATED"}))


def test_creates_seven_sign_profile():
    record = make_record()
    profile = engine().calculate(record, idempotency_key="vital:case:2026-08-04")
    assert len(profile["signs"]) == 7
    assert profile["available_count"] == 5
    assert profile["unavailable_count"] == 2
    assert profile["overall_score"] is not None
    assert record["counters"]["vital_profile_count"] == 1


def test_competition_and_content_are_unavailable():
    record = make_record()
    profile = engine().calculate(record, idempotency_key="vital:case:2026-08-04")
    signs = {item["code"]: item for item in profile["signs"]}
    assert signs["COMPETITION_RESILIENCE"]["status"] == "UNAVAILABLE"
    assert signs["CONTENT_INTEGRITY"]["status"] == "UNAVAILABLE"


def test_replay_is_idempotent():
    record = make_record()
    e = engine()
    first = e.calculate(record, idempotency_key="vital:case:2026-08-04")
    second = e.calculate(record, idempotency_key="vital:case:2026-08-04")
    assert first["profile_id"] == second["profile_id"]
    assert len(record["vital_profiles"]) == 1
    assert len(record["events"]) == 1
