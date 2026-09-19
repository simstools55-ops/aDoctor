from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.explainability import (
    ExplainableDiagnosisEngine,
    ExplainableDiagnosisService,
)


ROOT = Path(__file__).resolve().parents[2]


def test_explanation_is_recorded_and_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/explainability/medical_record.json")
        .read_text(encoding="utf-8")
    )
    policy = json.loads(
        (ROOT / "knowledge/explainability/explainability_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    service = ExplainableDiagnosisService(
        engine=ExplainableDiagnosisEngine(policy),
        event_log=MedicalRecordEventLog(
            {"DIAGNOSIS_EXPLANATION_CREATED"}
        ),
    )
    first = service.create(
        record,
        audience="USER",
        idempotency_key="explain:user:1",
    )
    second = service.create(
        record,
        audience="USER",
        idempotency_key="explain:user:1",
    )

    assert first["explanation_id"] == second["explanation_id"]
    assert len(record["diagnosis_explanations"]) == 1
    assert record["counters"]["diagnosis_explanation_count"] == 1
