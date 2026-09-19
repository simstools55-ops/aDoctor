from pathlib import Path
import json

from src.doctor.longitudinal import LongitudinalAnalyzer


ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (ROOT / "knowledge/longitudinal/longitudinal_profile_policy_v1.json")
    .read_text(encoding="utf-8")
)


def load():
    return json.loads(
        (ROOT / "tests/fixtures/longitudinal/chronic_case.json")
        .read_text(encoding="utf-8")
    )


def test_detects_chronic_recurrence():
    result = LongitudinalAnalyzer(POLICY).analyze(load())
    assert result["profile_status"] == "CHRONIC"
    assert result["recurrence"]["dominant_diagnosis"] == "CTR_PROBLEM"
    assert result["recurrence"]["maximum_recurrence_count"] == 3
    assert "CHRONIC_RECURRENCE" in result["patterns"]


def test_detects_treatment_resistance_when_not_recurrent():
    record = load()
    record["final_diagnoses"] = [
        {
            "diagnosis_id": "DX-1",
            "status": "CONFIRMED",
            "diagnosis_code": "CTR_PROBLEM",
        },
        {
            "diagnosis_id": "DX-2",
            "status": "CONFIRMED",
            "diagnosis_code": "CONTENT_STALE",
        },
    ]
    result = LongitudinalAnalyzer(POLICY).analyze(record)
    assert result["profile_status"] == "TREATMENT_RESISTANT"
    assert result["follow_up_priority"] == "HIGH"


def test_insufficient_history():
    record = load()
    record["final_diagnoses"] = record["final_diagnoses"][:1]
    result = LongitudinalAnalyzer(POLICY).analyze(record)
    assert result["profile_status"] == "INSUFFICIENT_HISTORY"
