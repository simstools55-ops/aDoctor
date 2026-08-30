from pathlib import Path
from datetime import datetime, timezone

from src.doctor.events import MedicalRecordEventLog
from src.doctor.evidence import EvidenceEngine
from src.doctor.knowledge import ClinicalKnowledgeBase


ROOT = Path(__file__).resolve().parents[2]


def engine():
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    return EvidenceEngine(ckb, MedicalRecordEventLog({"EVIDENCE_RECORDED"}))


def record_with_search(periods):
    return {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "events": [],
        "observations": [{
            "observation_id": "OBS-20260804-120000-ABCDEF",
            "observation_type": "SEARCH_CONSOLE",
            "observed_at": "2026-08-04T12:00:00+00:00",
            "source": "GOOGLE_SEARCH_CONSOLE",
            "schema_version": "1.0",
            "facts": {"periods": periods, "queries": [], "retrieval": {}},
        }],
        "evidence": [],
        "counters": {"evidence_count": 0},
        "updated_at": "2026-08-04T12:00:00+00:00",
    }


def test_extracts_ctr_evidence():
    record = record_with_search({
        "days_28": {"clicks": 5, "impressions": 1000, "ctr": 0.005, "position": 8.0},
        "days_90": {"clicks": 40, "impressions": 5000, "ctr": 0.008, "position": 8.0},
        "days_365": {"clicks": 100, "impressions": 15000, "ctr": 0.0067, "position": 8.5},
    })
    created = engine().extract_all(record)
    assert any(x["evidence_code"] == "CTR_BELOW_POSITION_EXPECTATION" for x in created)
    assert record["counters"]["evidence_count"] >= 1
    assert len(record["events"]) == len(record["evidence"])


def test_low_sample_is_recorded_not_discarded():
    record = record_with_search({
        "days_28": {"clicks": 0, "impressions": 20, "ctr": 0.0, "position": 8.0},
        "days_90": {"clicks": 1, "impressions": 60, "ctr": 0.0167, "position": 8.0},
        "days_365": {"clicks": 3, "impressions": 100, "ctr": 0.03, "position": 8.0},
    })
    created = engine().extract_all(record)
    ctr = next(x for x in created if x["evidence_code"] == "CTR_BELOW_POSITION_EXPECTATION")
    assert ctr["low_sample"] is True


def test_duplicate_evidence_is_not_created():
    record = record_with_search({
        "days_28": {"clicks": 5, "impressions": 1000, "ctr": 0.005, "position": 8.0},
        "days_90": {"clicks": 40, "impressions": 5000, "ctr": 0.008, "position": 8.0},
        "days_365": {"clicks": 100, "impressions": 15000, "ctr": 0.0067, "position": 8.5},
    })
    e = engine()
    e.extract_all(record)
    before = len(record["evidence"])
    second = e.extract_all(record)
    assert second == []
    assert len(record["evidence"]) == before


def test_long_time_since_update():
    record = {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "events": [],
        "observations": [{
            "observation_id": "OBS-20260804-120000-ABCDEF",
            "observation_type": "METADATA",
            "observed_at": "2026-08-04T12:00:00+00:00",
            "source": "ARTICLE",
            "schema_version": "1.0",
            "facts": {"last_modified_at": "2025-01-01T00:00:00+00:00"},
        }],
        "evidence": [],
        "counters": {"evidence_count": 0},
        "updated_at": "2026-08-04T12:00:00+00:00",
    }
    created = engine().extract_all(record)
    assert created[0]["evidence_code"] == "LONG_TIME_SINCE_UPDATE"
