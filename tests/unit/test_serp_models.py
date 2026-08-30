from pathlib import Path
import json
import pytest

from src.doctor.serp import SerpObservationInput


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/serp/complete_serp.json").read_text(encoding="utf-8")
    )


def test_parses_valid_serp_input():
    item = SerpObservationInput.from_dict(load())
    assert item.intent_primary == "HOW_TO"
    assert item.results[0].position == 1


def test_rejects_duplicate_positions():
    data = load()
    data["results"][1]["position"] = 1
    with pytest.raises(ValueError, match="unique and ordered"):
        SerpObservationInput.from_dict(data)
