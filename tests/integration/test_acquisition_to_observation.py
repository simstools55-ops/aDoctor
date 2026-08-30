from datetime import date
from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.search_console import SearchConsoleObservationInput, SearchConsoleObservationService
from src.doctor.search_console.acquisition import (
    SearchAnalyticsResponse, SearchAnalyticsRow, SearchConsoleAcquisitionService
)


ROOT = Path(__file__).resolve().parents[2]
POLICY = json.loads(
    (ROOT / "knowledge/observation/search_console/acquisition_policy_v1.json")
    .read_text(encoding="utf-8")
)


class Provider:
    def query(self, request):
        if request.dimensions:
            return SearchAnalyticsResponse(rows=(
                SearchAnalyticsRow(("test query",), 3, 100, 0.03, 7.0),
            ))
        return SearchAnalyticsResponse(rows=(
            SearchAnalyticsRow((), 3, 100, 0.03, 7.0),
        ))


def test_acquisition_output_records_as_observation():
    raw = SearchConsoleAcquisitionService(
        Provider(), POLICY, sleep=lambda _: None
    ).acquire(
        case_id="CASE-20260804-000001",
        site_id="sample-site",
        article_id="A000001",
        site_url="sc-domain:example.com",
        page_url="https://example.invalid/entry/example",
        today=date(2026, 8, 4),
    )
    parsed = SearchConsoleObservationInput.from_dict(raw)
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
        "counters": {"observation_count": 0},
        "case_status": "READY_FOR_OBSERVATION",
    }
    service = SearchConsoleObservationService(
        MedicalRecordEventLog({"OBSERVATION_RECORDED"})
    )
    observation = service.record(record, parsed, idempotency_key="gsc:test")
    assert observation["facts"]["retrieval"]["status"] == "COMPLETE"
    assert observation["facts"]["queries"][0]["query"] == "test query"
