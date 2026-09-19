from pathlib import Path
import json

from src.doctor.batch import BatchDoctorRunner, BatchPriorityCalculator, BatchRequest


ROOT = Path(__file__).resolve().parents[2]


def load_request():
    return BatchRequest.from_dict(json.loads(
        (ROOT / "tests/fixtures/batch/batch_request.json")
        .read_text(encoding="utf-8")
    ))


def load_policy():
    return json.loads(
        (ROOT / "knowledge/batch/batch_policy_v1.json")
        .read_text(encoding="utf-8")
    )


def test_batch_continues_after_case_failure():
    def execute(item, case_id, run_key):
        if item.article_id == "A2":
            raise RuntimeError("simulated failure")
        return {
            "contract_name": "SIMS_DOCTOR_SINGLE_CASE_RESULT_V1",
            "result_status": "DIAGNOSED",
            "referral": {"target": "WRITER"},
        }

    policy = load_policy()
    runner = BatchDoctorRunner(
        policy=policy,
        priority_calculator=BatchPriorityCalculator(policy),
        single_case_executor=execute,
    )
    result = runner.run(load_request())

    assert result["status"] == "COMPLETED_WITH_ERRORS"
    assert result["summary"]["completed"] == 1
    assert result["summary"]["failed"] == 1
    assert result["summary"]["writer_referrals"] == 1
    assert result["items"][0]["article_id"] == "A1"


def test_resume_skips_completed_item_and_retries_failed_item():
    calls = []

    def execute(item, case_id, run_key):
        calls.append(item.article_id)
        return {
            "contract_name": "SIMS_DOCTOR_SINGLE_CASE_RESULT_V1",
            "result_status": "FOLLOW_UP",
            "referral": {"target": "OBSERVATION"},
        }

    previous = {
        "items": [
            {
                "item_id": "ITEM-1",
                "article_id": "A1",
                "priority_score": 99,
                "status": "COMPLETED",
                "attempts": 1,
                "case_id": "BCASE-OLD1",
                "result": {"result_status": "DIAGNOSED", "referral": {"target": "WRITER"}},
                "error": None,
            },
            {
                "item_id": "ITEM-2",
                "article_id": "A2",
                "priority_score": 20,
                "status": "FAILED",
                "attempts": 1,
                "case_id": "BCASE-OLD2",
                "result": None,
                "error": {"code": "RuntimeError", "message": "failure"},
            },
        ]
    }
    policy = load_policy()
    runner = BatchDoctorRunner(
        policy=policy,
        priority_calculator=BatchPriorityCalculator(policy),
        single_case_executor=execute,
    )
    result = runner.run(load_request(), previous_result=previous)

    assert calls == ["A2"]
    statuses = {item["article_id"]: item["status"] for item in result["items"]}
    assert statuses["A1"] == "SKIPPED"
    assert statuses["A2"] == "COMPLETED"
    assert result["summary"]["follow_up"] == 1
