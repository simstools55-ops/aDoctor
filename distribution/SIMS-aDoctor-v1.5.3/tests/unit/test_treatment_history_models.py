from pathlib import Path
import json
import pytest

from src.doctor.treatment_history import TreatmentHistoryInput


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/treatment_history/worsened.json")
        .read_text(encoding="utf-8")
    )


def test_valid_input_parses():
    item = TreatmentHistoryInput.from_dict(load())
    assert item.assessment["classification"] == "WORSENED"


def test_duplicate_checkpoint_is_rejected():
    data = load()
    data["checkpoints"].append(dict(data["checkpoints"][-1]))
    with pytest.raises(ValueError, match="unique and chronological"):
        TreatmentHistoryInput.from_dict(data)
