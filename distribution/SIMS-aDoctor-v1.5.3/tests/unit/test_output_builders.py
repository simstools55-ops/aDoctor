from pathlib import Path
import json
import pytest

from src.doctor.output import SingleCaseResultBuilder, WriterRequestBuilder, WriterRequestError


ROOT = Path(__file__).resolve().parents[2]


def load():
    return json.loads(
        (ROOT / "tests/fixtures/output/confirmed_writer_case.json").read_text(encoding="utf-8")
    )


def test_builds_single_case_result():
    result = SingleCaseResultBuilder().build(load())
    assert result["contract_name"] == "SIMS_DOCTOR_SINGLE_CASE_RESULT_V1"
    assert result["diagnosis"]["code"] == "CONTENT_STALE"
    assert result["referral"]["target"] == "WRITER"


def test_builds_writer_request():
    result = WriterRequestBuilder().build(load())
    assert result["contract_name"] == "SIMS_DOCTOR_WRITER_REQUEST_V1"
    assert result["diagnosis"]["code"] == "CONTENT_STALE"
    assert result["preservation"]["preserve_ads_and_links"] is True


def test_deferred_case_cannot_build_writer_request():
    data = load()
    data["final_diagnoses"][0]["status"] = "DEFERRED"
    data["final_diagnoses"][0]["diagnosis_code"] = None
    with pytest.raises(WriterRequestError):
        WriterRequestBuilder().build(data)
