import json
from pathlib import Path
import pytest

from doctor.common.errors import DoctorError, INVALID_JSON, MISSING_REQUIRED_FIELD, UNSUPPORTED_VERSION
from doctor.receiver.request_receiver import receive_request

ROOT = Path(__file__).resolve().parents[2]


def fixture(name):
    return json.loads((ROOT / "tests" / "fixtures" / name).read_text(encoding="utf-8"))


def test_valid_request_is_normalized_without_mutating_raw():
    payload = fixture("valid/single_case_request.json")
    payload["article"]["title"] = "  テスト記事  "
    received = receive_request(payload)
    assert received.raw_request["article"]["title"] == "  テスト記事  "
    assert received.normalized_request["article"]["title"] == "テスト記事"


def test_invalid_json_rejected():
    with pytest.raises(DoctorError) as exc:
        receive_request("{invalid")
    assert exc.value.code == INVALID_JSON


def test_missing_article_id_rejected():
    payload = fixture("invalid/missing_article_id.json")
    with pytest.raises(DoctorError) as exc:
        receive_request(payload)
    assert exc.value.code == MISSING_REQUIRED_FIELD
    assert exc.value.field == "article.article_id"


def test_unsupported_version_rejected():
    payload = fixture("invalid/unsupported_version.json")
    with pytest.raises(DoctorError) as exc:
        receive_request(payload)
    assert exc.value.code == UNSUPPORTED_VERSION
