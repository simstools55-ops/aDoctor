from datetime import datetime, timezone
from pathlib import Path
import json

from src.doctor.api import (
    DoctorApiApp, InMemoryAuditLog, InMemoryIdempotencyStore
)
from src.doctor.batch import BatchPriorityCalculator
from src.doctor.batch.queue import BatchQueueService, InMemoryBatchQueueRepository
from src.doctor.integration.sbm import SbmBatchGateway
from src.doctor.security import (
    HmacAuthenticator, InMemoryNonceStore, InMemoryRateLimiter
)


ROOT = Path(__file__).resolve().parents[2]
SECRET = "test-secret"


def build():
    queue_policy = json.loads(
        (ROOT / "knowledge/batch/batch_queue_policy_v1.json").read_text(encoding="utf-8")
    )
    batch_policy = json.loads(
        (ROOT / "knowledge/batch/batch_policy_v1.json").read_text(encoding="utf-8")
    )
    service = BatchQueueService(
        repository=InMemoryBatchQueueRepository(),
        policy=queue_policy,
        priority_calculator=BatchPriorityCalculator(batch_policy),
    )
    api = DoctorApiApp(
        gateway=SbmBatchGateway(service),
        authenticator=HmacAuthenticator(
            client_secrets={"sbm": SECRET},
            nonce_store=InMemoryNonceStore(),
        ),
        rate_limiter=InMemoryRateLimiter(
            requests_per_minute=60, burst=20
        ),
        idempotency_store=InMemoryIdempotencyStore(),
        audit_log=InMemoryAuditLog(),
    )
    return service, api


def signed(method, path, body, nonce, key=None):
    timestamp = datetime.now(timezone.utc).isoformat()
    signature = HmacAuthenticator.sign(
        secret=SECRET,
        method=method,
        path=path,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
    )
    headers = {
        "X-SIMS-Client-Id": "sbm",
        "X-SIMS-Timestamp": timestamp,
        "X-SIMS-Nonce": nonce,
        "X-SIMS-Signature": signature,
    }
    if key:
        headers["Idempotency-Key"] = key
    return headers


def test_submit_and_status():
    _, api = build()
    payload = json.loads(
        (ROOT / "tests/fixtures/sbm_batch/request.json").read_text(encoding="utf-8")
    )
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    response = api.handle(
        method="POST",
        path="/v1/sbm/batches",
        headers=signed("POST", "/v1/sbm/batches", body, "n1", "idem-1"),
        body=body,
    )
    assert response.status_code == 202
    queue_id = response.body["queue_record_id"]

    status = api.handle(
        method="GET",
        path=f"/v1/sbm/batches/{queue_id}",
        headers=signed("GET", f"/v1/sbm/batches/{queue_id}", b"", "n2"),
    )
    assert status.status_code == 200
    assert status.body["status"] == "QUEUED"


def test_idempotent_replay_returns_same_response():
    _, api = build()
    payload = json.loads(
        (ROOT / "tests/fixtures/sbm_batch/request.json").read_text(encoding="utf-8")
    )
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    first = api.handle(
        method="POST",
        path="/v1/sbm/batches",
        headers=signed("POST", "/v1/sbm/batches", body, "n3", "idem-2"),
        body=body,
    )
    second = api.handle(
        method="POST",
        path="/v1/sbm/batches",
        headers=signed("POST", "/v1/sbm/batches", body, "n4", "idem-2"),
        body=body,
    )
    assert first.body == second.body
    assert second.headers["Idempotent-Replay"] == "true"


def test_invalid_signature_is_rejected():
    _, api = build()
    response = api.handle(
        method="GET",
        path="/v1/sbm/batches/unknown",
        headers={
            "X-SIMS-Client-Id": "sbm",
            "X-SIMS-Timestamp": datetime.now(timezone.utc).isoformat(),
            "X-SIMS-Nonce": "bad",
            "X-SIMS-Signature": "bad",
        },
    )
    assert response.status_code == 401
    assert response.body["error"]["code"] == "AUTHENTICATION_FAILED"
