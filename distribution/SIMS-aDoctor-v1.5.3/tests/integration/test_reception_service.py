from datetime import datetime, timezone
import json
from pathlib import Path

from doctor.service import DoctorReceptionService

ROOT = Path(__file__).resolve().parents[2]


class FixedClock:
    def now(self):
        return datetime(2026, 8, 4, 10, 0, 0, tzinfo=timezone.utc)


def payload():
    return json.loads((ROOT / "tests/fixtures/valid/single_case_request.json").read_text(encoding="utf-8"))


def test_new_case_creates_registry_and_record():
    service = DoctorReceptionService(clock=FixedClock())
    result = service.accept(payload())
    assert result["status"] == "ACCEPTED"
    case = service.registry.get(result["case_id"])
    record = service.records.get(result["medical_record_id"])
    assert case["medical_record_id"] == record["medical_record_id"]
    assert record["case_id"] == case["case_id"]


def test_active_case_is_reused():
    service = DoctorReceptionService(clock=FixedClock())
    first = service.accept(payload())
    second = service.accept(payload())
    assert second["status"] == "EXISTING_CASE_REUSED"
    assert second["case_id"] == first["case_id"]
    record = service.records.get(first["medical_record_id"])
    assert record["counters"]["request_count"] == 2


def test_same_article_id_in_another_site_creates_new_case():
    service = DoctorReceptionService(clock=FixedClock())
    first = service.accept(payload())
    other = payload()
    other["site"]["site_id"] = "another-site"
    other["site"]["site_name"] = "別サイト"
    second = service.accept(other)
    assert second["status"] == "ACCEPTED"
    assert second["case_id"] != first["case_id"]


def test_invalid_request_returns_stable_error_contract():
    service = DoctorReceptionService(clock=FixedClock())
    invalid = payload()
    del invalid["article"]["article_id"]
    result = service.accept(invalid)
    assert result["status"] == "REJECTED"
    assert result["error"]["code"] == "MISSING_REQUIRED_FIELD"
    assert result["case_id"] is None
