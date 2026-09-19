from pathlib import Path
import json
import pytest

from src.doctor.batch import BatchRequest


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/batch/batch_request.json")
        .read_text(encoding="utf-8")
    )


def test_parses_batch_request():
    request = BatchRequest.from_dict(load())
    assert len(request.items) == 2
    assert request.items[0].article_id == "A1"


def test_duplicate_article_is_rejected():
    data = load()
    data["items"][1]["article_id"] = "A1"
    with pytest.raises(ValueError, match="Duplicate article ID"):
        BatchRequest.from_dict(data)
