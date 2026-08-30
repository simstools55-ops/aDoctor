from pathlib import Path
import json

from src.doctor.batch import BatchPriorityCalculator, BatchRequest


ROOT = Path(__file__).resolve().parents[2]


def test_urgent_article_has_higher_priority():
    request = BatchRequest.from_dict(json.loads(
        (ROOT / "tests/fixtures/batch/batch_request.json")
        .read_text(encoding="utf-8")
    ))
    policy = json.loads(
        (ROOT / "knowledge/batch/batch_policy_v1.json")
        .read_text(encoding="utf-8")
    )
    calculator = BatchPriorityCalculator(policy)
    assert calculator.calculate(request.items[0]) > calculator.calculate(request.items[1])
