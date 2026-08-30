from pathlib import Path
import json

from src.doctor.article_snapshot import ArticleSnapshotInput, ArticleSnapshotService
from src.doctor.events import MedicalRecordEventLog
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.vital_signs import VitalSignsEngine


ROOT = Path(__file__).resolve().parents[2]


def test_article_snapshot_enables_content_integrity():
    raw = json.loads(
        (ROOT / "tests/fixtures/article_snapshot/complete_snapshot.json")
        .read_text(encoding="utf-8")
    )
    parsed = ArticleSnapshotInput.from_dict(raw)
    record = {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "patient": {
            "site_id": "sample-site",
            "article_id": "A000001",
            "article_url": "https://example.invalid/entry/example",
        },
        "events": [],
        "observations": [],
        "evidence": [],
        "vital_profiles": [],
        "counters": {"observation_count": 0, "vital_profile_count": 0},
        "case_status": "READY_FOR_OBSERVATION",
    }
    log = MedicalRecordEventLog({"OBSERVATION_RECORDED", "VITAL_SIGNS_CALCULATED"})
    ArticleSnapshotService(log).record(record, parsed, idempotency_key="article:test")
    ckb = ClinicalKnowledgeBase(ROOT / "knowledge").load()
    profile = VitalSignsEngine(ckb, log).calculate(
        record, idempotency_key="vital:article:test"
    )
    signs = {item["code"]: item for item in profile["signs"]}
    assert signs["CONTENT_INTEGRITY"]["status"] == "AVAILABLE"
    assert signs["CONTENT_INTEGRITY"]["score"] >= 80
