from pathlib import Path
import json

from src.doctor.algorithm_impact import AlgorithmImpactEngine, AlgorithmImpactService
from src.doctor.events import MedicalRecordEventLog

ROOT = Path(__file__).resolve().parents[2]


def test_algorithm_assessment_is_recorded_and_idempotent():
    policy = json.loads((ROOT / "knowledge/algorithm_impact/algorithm_impact_policy_v1.json").read_text(encoding="utf-8"))
    record = {
        "case_id": "CASE-1", "medical_record_id": "MR-1", "events": [], "counters": {},
        "algorithm_context": {
            "update": {"detected": True, "source_status": "OFFICIAL_CONFIRMED", "rollout_status": "IN_PROGRESS"},
            "correlation": {"temporal": "HIGH", "site_wide": "HIGH", "segment": "MEDIUM", "article": "HIGH", "serp": "HIGH"}
        }
    }
    service = AlgorithmImpactService(
        engine=AlgorithmImpactEngine(policy),
        event_log=MedicalRecordEventLog({"ALGORITHM_IMPACT_ASSESSED"}),
    )
    first = service.assess(record, idempotency_key="algorithm:1")
    second = service.assess(record, idempotency_key="algorithm:1")
    assert first["assessment_id"] == second["assessment_id"]
    assert len(record["algorithm_impact_assessments"]) == 1
