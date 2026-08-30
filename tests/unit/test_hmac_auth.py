from datetime import datetime, timezone
import pytest

from src.doctor.security import HmacAuthenticator, AuthenticationError, InMemoryNonceStore


def headers(secret, method, path, body, nonce="n1"):
    timestamp = datetime.now(timezone.utc).isoformat()
    signature = HmacAuthenticator.sign(
        secret=secret,
        method=method,
        path=path,
        timestamp=timestamp,
        nonce=nonce,
        body=body,
    )
    return {
        "X-SIMS-Client-Id": "sbm",
        "X-SIMS-Timestamp": timestamp,
        "X-SIMS-Nonce": nonce,
        "X-SIMS-Signature": signature,
    }


def test_authenticates_valid_signature():
    auth = HmacAuthenticator(
        client_secrets={"sbm": "secret"},
        nonce_store=InMemoryNonceStore(),
    )
    result = auth.authenticate(
        method="POST",
        path="/v1/sbm/batches",
        headers=headers("secret", "POST", "/v1/sbm/batches", b"{}"),
        body=b"{}",
    )
    assert result == "sbm"


def test_replay_is_rejected():
    auth = HmacAuthenticator(
        client_secrets={"sbm": "secret"},
        nonce_store=InMemoryNonceStore(),
    )
    h = headers("secret", "POST", "/v1/sbm/batches", b"{}")
    auth.authenticate(
        method="POST", path="/v1/sbm/batches", headers=h, body=b"{}"
    )
    with pytest.raises(AuthenticationError, match="Replay"):
        auth.authenticate(
            method="POST", path="/v1/sbm/batches", headers=h, body=b"{}"
        )
