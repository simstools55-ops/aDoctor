from pathlib import Path

from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.vital_signs import VitalSignsEngine


ROOT = Path(__file__).resolve().parents[2]


def test_vital_profile_is_recorded_in_event_log():
    record = {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "events": [],
        "observations": [{
            "observation_id": "OBS-20260804-120000-ABCDEF",
            "observation_type": "SEARCH_CONSOLE",
            "observed_at": "2026-08-04T12:00:00+00:00",
            "source": "GOOGLE_SEARCH_CONSOLE",
            "schema_version": "1.0",
            "facts": {
                "periods": {
                    "days_28": {"clicks": 10, "impressions": 1000, "ctr": 0.01, "position": 8.0},
                    "days_90": {"clicks": 30, "impressions": 3000, "ctr": 0.01, "position": 8.0},
                    "days_365": {"clicks": 120, "impressions": 12000, "ctr": 0.01, "position": 8.0}
                },
                "queries": [],
                "retrieval": {}
            }
        }],
        "evidence": [],
        "vital_profiles": [],
        "counters": {"vital_profile_count": 0},
        "updated_at": "2026-08-04T12:00:00+00:00"
    }
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    engine = VitalSignsEngine(ckb, MedicalRecordEventLog({"VITAL_SIGNS_CALCULATED"}))
    profile = engine.calculate(record, idempotency_key="vital:test")

    assert record["events"][0]["event_type"] == "VITAL_SIGNS_CALCULATED"
    assert record["events"][0]["payload"]["vital_profile"]["profile_id"] == profile["profile_id"]
