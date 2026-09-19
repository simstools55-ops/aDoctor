from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.vital_score import VitalScoreEngine, VitalScoreService


ROOT = Path(__file__).resolve().parents[2]


def test_score_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/vital_score/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/vital_score/vital_score_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = VitalScoreService(
        engine=VitalScoreEngine(policy),
        event_log=MedicalRecordEventLog({"VITAL_SCORE_CALCULATED"}),
    )
    first = service.calculate(record, idempotency_key="score:1")
    second = service.calculate(record, idempotency_key="score:1")

    assert first["score_id"] == second["score_id"]
    assert len(record["vital_scores"]) == 1
    assert record["counters"]["vital_score_count"] == 1
