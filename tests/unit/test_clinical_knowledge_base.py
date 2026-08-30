from pathlib import Path
import json
import shutil

import pytest

from src.doctor.knowledge import ClinicalKnowledgeBase, KnowledgeValidationError


ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "knowledge"


def test_ckb_loads_and_exposes_known_codes():
    ckb = ClinicalKnowledgeBase(KNOWLEDGE).load()
    assert ckb.is_known_code("observation", "SEARCH_CONSOLE")
    assert ckb.is_known_code("evidence", "CTR_BELOW_POSITION_EXPECTATION")
    assert ckb.is_known_code("vital_signs", "CTR_HEALTH")
    assert ckb.is_known_code("findings", "CTR_UNDERPERFORMING")


@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (100, "NORMAL"),
        (90, "NORMAL"),
        (89, "MILD_ATTENTION"),
        (70, "MILD_ATTENTION"),
        (69, "OBSERVATION_REQUIRED"),
        (50, "OBSERVATION_REQUIRED"),
        (49, "TREATMENT_REQUIRED"),
        (30, "TREATMENT_REQUIRED"),
        (29, "SEVERE"),
        (0, "SEVERE"),
    ],
)
def test_vital_score_classification(score, expected):
    ckb = ClinicalKnowledgeBase(KNOWLEDGE).load()
    assert ckb.classify_vital_score(score) == expected


def test_unknown_registry_is_rejected():
    ckb = ClinicalKnowledgeBase(KNOWLEDGE).load()
    with pytest.raises(KeyError):
        ckb.codes("diagnosis")


def test_duplicate_code_is_rejected(tmp_path):
    copied = tmp_path / "knowledge"
    shutil.copytree(KNOWLEDGE, copied)
    path = copied / "findings" / "finding_codes.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["items"].append(dict(data["items"][0]))
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    with pytest.raises(KnowledgeValidationError, match="Duplicate code"):
        ClinicalKnowledgeBase(copied).load()
