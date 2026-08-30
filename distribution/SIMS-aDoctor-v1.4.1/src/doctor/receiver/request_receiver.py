from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any, Dict, Mapping, Union

from doctor.common.errors import DoctorError, INVALID_JSON, INVALID_FIELD_TYPE
from doctor.receiver.request_normalizer import normalize_request
from doctor.receiver.request_validator import validate_request
from doctor.receiver.sbm_v2_adapter import adapt_sbm_v2, is_sbm_v2


@dataclass(frozen=True)
class ReceivedRequest:
    raw_request: Dict[str, Any]
    normalized_request: Dict[str, Any]


def receive_request(payload: Union[str, bytes, Mapping[str, Any]]) -> ReceivedRequest:
    if isinstance(payload, bytes):
        try:
            payload = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DoctorError(INVALID_JSON, "request must be UTF-8 JSON") from exc

    if isinstance(payload, str):
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise DoctorError(INVALID_JSON, "request is not valid JSON") from exc
    elif isinstance(payload, Mapping):
        parsed = dict(payload)
    else:
        raise DoctorError(INVALID_FIELD_TYPE, "request must be JSON text or an object", "request")

    intake = adapt_sbm_v2(parsed) if is_sbm_v2(parsed) else parsed
    validate_request(intake)
    normalized = normalize_request(intake)
    return ReceivedRequest(raw_request=parsed, normalized_request=normalized)
