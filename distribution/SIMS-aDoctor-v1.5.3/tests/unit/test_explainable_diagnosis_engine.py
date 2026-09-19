from pathlib import Path
import json

from src.doctor.explainability import ExplainableDiagnosisEngine


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/explainability/medical_record.json")
        .read_text(encoding="utf-8")
    )


def policy():
    return json.loads(
        (ROOT / "knowledge/explainability/explainability_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_user_explanation_hides_internal_ids():
    record = load()
    result = ExplainableDiagnosisEngine(policy()).explain(
        record,
        record["composite_diagnoses"][-1],
        record["treatment_recommendations"][-1],
        audience="USER",
    )
    assert result["audience"] == "USER"
    assert "supporting_assessments" not in result["trace"]
    assert result["decision_path"][-1]["step"] == "FINAL_DIAGNOSIS"


def test_system_explanation_contains_trace():
    record = load()
    result = ExplainableDiagnosisEngine(policy()).explain(
        record,
        record["composite_diagnoses"][-1],
        record["treatment_recommendations"][-1],
        audience="SYSTEM",
    )
    assert "supporting_assessments" in result["trace"]
    assert "score" in result["trace"]


def test_winner_query_is_explained_as_blocking_factor():
    record = load()
    record["composite_diagnoses"][-1]["safety"][
        "winner_query_protected"
    ] = True
    result = ExplainableDiagnosisEngine(policy()).explain(
        record,
        record["composite_diagnoses"][-1],
        record["treatment_recommendations"][-1],
        audience="USER",
    )
    codes = [item["code"] for item in result["blocking_factors"]]
    assert "WINNER_QUERY_PROTECTION" in codes
