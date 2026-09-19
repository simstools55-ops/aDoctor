from pathlib import Path
import json

from src.doctor.composite_diagnosis import CompositeDiagnosisEngine


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/composite_diagnosis/medical_record.json")
        .read_text(encoding="utf-8")
    )


def policy():
    return json.loads(
        (ROOT / "knowledge/composite_diagnosis/composite_diagnosis_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_local_optimization():
    result = CompositeDiagnosisEngine(policy()).diagnose(load())
    assert result["final_diagnosis"] == "LOCAL_OPTIMIZATION"
    assert result["safety"]["full_rewrite_allowed"] is True


def test_low_sample_forces_follow_up():
    record = load()
    record["ctr_opportunity_assessments"][0]["metrics"]["low_sample"] = True
    result = CompositeDiagnosisEngine(policy()).diagnose(record)
    assert result["final_diagnosis"] == "FOLLOW_UP_REQUIRED"


def test_recent_update_forces_observation():
    record = load()
    record["freshness_decay_assessments"][0]["classification"] = "RECENT_UPDATE_OBSERVATION"
    result = CompositeDiagnosisEngine(policy()).diagnose(record)
    assert result["final_diagnosis"] == "OBSERVE_ONLY"


def test_merge_candidate_has_priority():
    record = load()
    record["cannibalization_assessments"][0]["classification"] = "MERGE_CANDIDATE"
    result = CompositeDiagnosisEngine(policy()).diagnose(record)
    assert result["final_diagnosis"] == "MERGE_RECOMMENDED"


def test_winner_query_blocks_full_rewrite():
    record = load()
    record["intent_drift_assessments"][0]["classification"] = "TOPIC_DISPERSION"
    record["freshness_decay_assessments"][0]["classification"] = "SEVERE_FRESHNESS_DECAY"
    record["ctr_opportunity_assessments"][0]["protections"]["winner_query_protected"] = True
    result = CompositeDiagnosisEngine(policy()).diagnose(record)
    assert result["final_diagnosis"] in {"LOCAL_OPTIMIZATION", "OBSERVE_ONLY"}
    assert result["safety"]["full_rewrite_allowed"] is False
