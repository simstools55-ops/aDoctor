from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.longitudinal import LongitudinalAnalyzer, LongitudinalProfileService


ROOT = Path(__file__).resolve().parents[2]


def test_generates_and_persists_longitudinal_profile():
    record = json.loads(
        (ROOT / "tests/fixtures/longitudinal/chronic_case.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/longitudinal/longitudinal_profile_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = LongitudinalProfileService(
        LongitudinalAnalyzer(policy),
        MedicalRecordEventLog({"LONGITUDINAL_PROFILE_UPDATED"}),
    )
    profile = service.generate(record, idempotency_key="longitudinal:1")

    assert profile["profile_status"] == "CHRONIC"
    assert profile["follow_up_priority"] == "URGENT"
    assert record["events"][0]["event_type"] == "LONGITUDINAL_PROFILE_UPDATED"
    assert record["counters"]["longitudinal_profile_count"] == 1


def test_longitudinal_profile_is_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/longitudinal/chronic_case.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/longitudinal/longitudinal_profile_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = LongitudinalProfileService(
        LongitudinalAnalyzer(policy),
        MedicalRecordEventLog({"LONGITUDINAL_PROFILE_UPDATED"}),
    )
    first = service.generate(record, idempotency_key="longitudinal:2")
    second = service.generate(record, idempotency_key="longitudinal:2")

    assert first["profile_id"] == second["profile_id"]
    assert len(record["longitudinal_profiles"]) == 1
