from copy import deepcopy
from datetime import datetime, timezone

import pytest

from src.doctor.events import MedicalRecordEventLog, EventLogError


ALLOWED = {"OBSERVATION_RECORDED", "PROCESSING_ERROR"}


def record():
    return {
        "case_id": "CASE-20260804-000001",
        "medical_record_id": "MR-CASE-20260804-000001",
        "events": [],
        "updated_at": "2026-08-04T00:00:00+00:00",
    }


def test_append_event_and_idempotent_reuse():
    log = MedicalRecordEventLog(ALLOWED)
    medical_record = record()
    first = log.append(
        medical_record,
        event_type="OBSERVATION_RECORDED",
        payload={"value": 1},
        occurred_at=datetime(2026, 8, 4, tzinfo=timezone.utc),
        idempotency_key="gsc:case:2026-08-04",
    )
    second = log.append(
        medical_record,
        event_type="OBSERVATION_RECORDED",
        payload={"value": 1},
        occurred_at=datetime(2026, 8, 5, tzinfo=timezone.utc),
        idempotency_key="gsc:case:2026-08-04",
    )
    assert first.event_id == second.event_id
    assert len(medical_record["events"]) == 1


def test_idempotency_conflict_is_rejected():
    log = MedicalRecordEventLog(ALLOWED)
    medical_record = record()
    log.append(
        medical_record,
        event_type="OBSERVATION_RECORDED",
        payload={"value": 1},
        idempotency_key="same",
    )
    with pytest.raises(EventLogError):
        log.append(
            medical_record,
            event_type="OBSERVATION_RECORDED",
            payload={"value": 2},
            idempotency_key="same",
        )


def test_event_payload_tampering_is_detected():
    log = MedicalRecordEventLog(ALLOWED)
    medical_record = record()
    log.append(
        medical_record,
        event_type="OBSERVATION_RECORDED",
        payload={"value": 1},
    )
    tampered = deepcopy(medical_record["events"])
    tampered[0]["payload"]["value"] = 99
    with pytest.raises(EventLogError, match="hash mismatch"):
        log.validate_existing(tampered)
