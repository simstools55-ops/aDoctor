from pathlib import Path
import json
import pytest

from src.doctor.article_snapshot import ArticleSnapshotInput


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/article_snapshot/complete_snapshot.json")
        .read_text(encoding="utf-8")
    )


def test_valid_snapshot_parses():
    item = ArticleSnapshotInput.from_dict(load())
    assert item.metrics["heading_count"] == 4
    assert item.intent_alignment["score"] == 90


def test_metric_mismatch_is_rejected():
    data = load()
    data["metrics"]["faq_count"] = 99
    with pytest.raises(ValueError, match="faq_count"):
        ArticleSnapshotInput.from_dict(data)
