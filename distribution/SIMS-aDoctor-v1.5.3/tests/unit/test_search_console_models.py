from pathlib import Path
import json

import pytest

from src.doctor.search_console import SearchConsoleObservationInput


ROOT = Path(__file__).resolve().parents[2]


def load():
    data = json.loads(
        (ROOT / "tests/fixtures/search_console/complete_365_days.json").read_text(encoding="utf-8")
    )
    return data


def test_complete_input_parses():
    item = SearchConsoleObservationInput.from_dict(load())
    assert item.status == "COMPLETE"
    assert item.periods["days_365"].impressions == 18000


def test_failed_input_requires_error_code():
    data = load()
    data["retrieval"]["status"] = "FAILED"
    with pytest.raises(ValueError, match="error_code"):
        SearchConsoleObservationInput.from_dict(data)


def test_all_required_periods_are_required():
    data = load()
    del data["periods"]["days_90"]
    with pytest.raises(ValueError, match="28, 90, and 365"):
        SearchConsoleObservationInput.from_dict(data)
