from src.doctor.security import (
    SQLiteSecurityState, SQLiteNonceStore,
    SQLiteIdempotencyStore, SQLiteAuditLog
)


def test_nonce_persists_across_instances(tmp_path):
    path = tmp_path / "security.db"
    first = SQLiteNonceStore(SQLiteSecurityState(path))
    assert first.claim("sbm", "nonce-1", ttl_seconds=600) is True

    second = SQLiteNonceStore(SQLiteSecurityState(path))
    assert second.claim("sbm", "nonce-1", ttl_seconds=600) is False


def test_idempotency_persists_across_instances(tmp_path):
    path = tmp_path / "security.db"
    first = SQLiteIdempotencyStore(SQLiteSecurityState(path))
    first.put("sbm", "key-1", {"accepted": True}, ttl_hours=24)

    second = SQLiteIdempotencyStore(SQLiteSecurityState(path))
    assert second.get("sbm", "key-1") == {"accepted": True}


def test_audit_log_persists(tmp_path):
    state = SQLiteSecurityState(tmp_path / "security.db")
    log = SQLiteAuditLog(state)
    log.append(
        client_id="sbm", method="GET", path="/health/live",
        status_code=200, event="API_REQUEST_COMPLETED"
    )
    assert state.audit_entries()[0]["event"] == "API_REQUEST_COMPLETED"
