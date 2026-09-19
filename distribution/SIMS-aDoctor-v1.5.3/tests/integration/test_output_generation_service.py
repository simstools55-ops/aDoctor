from pathlib import Path
import json

from src.doctor.events import MedicalRecordEventLog
from src.doctor.output import OutputGenerationService


ROOT = Path(__file__).resolve().parents[2]


def test_generates_result_and_writer_request_with_event():
    record = json.loads(
        (ROOT / "tests/fixtures/output/confirmed_writer_case.json").read_text(encoding="utf-8")
    )
    service = OutputGenerationService(MedicalRecordEventLog({"OUTPUT_GENERATED"}))
    outputs = service.generate(record, idempotency_key="output:1")

    assert outputs["single_case_result"]["result_status"] == "DIAGNOSED"
    assert outputs["writer_request"]["contract_name"] == "SIMS_DOCTOR_WRITER_REQUEST_V1"
    assert record["events"][0]["event_type"] == "OUTPUT_GENERATED"
    assert record["counters"]["output_count"] == 1


def test_output_generation_is_idempotent():
    record = json.loads(
        (ROOT / "tests/fixtures/output/confirmed_writer_case.json").read_text(encoding="utf-8")
    )
    service = OutputGenerationService(MedicalRecordEventLog({"OUTPUT_GENERATED"}))
    first = service.generate(record, idempotency_key="output:2")
    second = service.generate(record, idempotency_key="output:2")
    assert first == second
    assert len(record["outputs"]) == 1
