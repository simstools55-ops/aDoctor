from pathlib import Path

from src.doctor.events import MedicalRecordEventLog
from src.doctor.evidence import EvidenceEngine
from src.doctor.knowledge import ClinicalKnowledgeBase


ROOT = Path(__file__).resolve().parents[2]


def test_evidence_is_linked_to_source_observation_and_event():
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
                    "days_28": {"clicks": 5, "impressions": 1000, "ctr": 0.005, "position": 8.0},
                    "days_90": {"clicks": 40, "impressions": 5000, "ctr": 0.008, "position": 6.0},
                    "days_365": {"clicks": 100, "impressions": 15000, "ctr": 0.0067, "position": 7.0}
                },
                "queries": [],
                "retrieval": {}
            },
        }],
        "evidence": [],
        "counters": {"evidence_count": 0},
        "updated_at": "2026-08-04T12:00:00+00:00",
    }
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    engine = EvidenceEngine(ckb, MedicalRecordEventLog({"EVIDENCE_RECORDED"}))
    created = engine.extract_all(record)

    assert created
    assert all(item["source_observation_ids"] == ["OBS-20260804-120000-ABCDEF"] for item in created)
    assert all(event["event_type"] == "EVIDENCE_RECORDED" for event in record["events"])
    assert all("evidence" in event["payload"] for event in record["events"])
