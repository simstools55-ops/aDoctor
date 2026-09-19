from datetime import datetime, timezone
from pathlib import Path
import json

from src.doctor.config import DoctorSettings
from src.doctor.deployment import create_api
from src.doctor.security import HmacAuthenticator


ROOT = Path(__file__).resolve().parents[2]


def settings(tmp_path):
    return DoctorSettings(
        repository_root=ROOT,
        queue_database=tmp_path / "queue.db",
        security_database=tmp_path / "security.db",
        client_secrets={"sbm": "0123456789abcdef0123456789abcdef"},
    )


def signed(secret, method, path, body=b"", nonce="nonce"):
    timestamp = datetime.now(timezone.utc).isoformat()
    return {
        "X-SIMS-Client-Id": "sbm",
        "X-SIMS-Timestamp": timestamp,
        "X-SIMS-Nonce": nonce,
        "X-SIMS-Signature": HmacAuthenticator.sign(
            secret=secret, method=method, path=path,
            timestamp=timestamp, nonce=nonce, body=body
        ),
    }


def test_health_endpoints(tmp_path):
    api = create_api(settings(tmp_path))
    live = api.handle(
        method="GET", path="/health/live",
        headers=signed(
            "0123456789abcdef0123456789abcdef",
            "GET", "/health/live", nonce="live"
        )
    )
    ready = api.handle(
        method="GET", path="/health/ready",
        headers=signed(
            "0123456789abcdef0123456789abcdef",
            "GET", "/health/ready", nonce="ready"
        )
    )
    assert live.status_code == 200
    assert live.body["status"] == "LIVE"
    assert ready.status_code == 200
    assert ready.body["status"] == "READY"


def test_replay_protection_survives_api_restart(tmp_path):
    config = settings(tmp_path)
    path = "/health/live"
    headers = signed(
        "0123456789abcdef0123456789abcdef",
        "GET", path, nonce="persistent-nonce"
    )

    first_api = create_api(config)
    first = first_api.handle(method="GET", path=path, headers=headers)
    assert first.status_code == 200

    second_api = create_api(config)
    second = second_api.handle(method="GET", path=path, headers=headers)
    assert second.status_code == 401
    assert second.body["error"]["code"] == "AUTHENTICATION_FAILED"
