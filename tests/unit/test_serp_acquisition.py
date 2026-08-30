from pathlib import Path
import json

from src.doctor.serp.acquisition import (
    RawSerpResponse,
    RawSerpResult,
    SerpAcquisitionService,
)


ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (ROOT / "knowledge/observation/serp/serp_observation_policy_v1.json")
    .read_text(encoding="utf-8")
)


class Provider:
    def search(self, query, *, result_limit):
        return RawSerpResponse(
            results=(
                RawSerpResult(
                    1, "設定方法", "https://a.example/1", "a.example",
                    "手順", updated_at="2026-07-01", authority_score=80, intent_match=95
                ),
                RawSerpResult(
                    2, "設定ガイド", "https://b.example/2", "b.example",
                    "解説", authority_score=60, intent_match=85
                ),
            ),
            features=("PEOPLE_ALSO_ASK", "VIDEO"),
        )


def test_acquires_and_normalizes_serp():
    result = SerpAcquisitionService(Provider(), POLICY, sleep=lambda _: None).acquire(
        case_id="CASE-1",
        site_id="site",
        article_id="A1",
        article_url="https://site.example/a",
        query="windows 11 設定 方法",
    )
    assert result["retrieval"]["status"] == "COMPLETE"
    assert result["intent"]["primary"] == "HOW_TO"
    assert result["competition"]["strength_score"] > 0
    assert len(result["results"]) == 2


def test_compares_previous_serp():
    previous = {
        "observation_id": "OBS-OLD",
        "facts": {
            "intent": {"primary": "INFORMATIONAL"},
            "features": ["IMAGE_PACK"],
            "results": [{"domain": "old.example"}],
        },
    }
    result = SerpAcquisitionService(Provider(), POLICY, sleep=lambda _: None).acquire(
        case_id="CASE-1",
        site_id="site",
        article_id="A1",
        article_url="https://site.example/a",
        query="windows 11 設定 方法",
        previous_observation=previous,
    )
    assert result["comparison"]["intent_changed"] is True
    assert "old.example" in result["comparison"]["lost_domains"]
    assert "a.example" in result["comparison"]["new_domains"]
