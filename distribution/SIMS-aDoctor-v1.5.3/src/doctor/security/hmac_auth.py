from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
from typing import Mapping

from .nonce_store import InMemoryNonceStore


class AuthenticationError(ValueError):
    pass


class HmacAuthenticator:
    def __init__(
        self,
        *,
        client_secrets: Mapping[str, str],
        nonce_store: InMemoryNonceStore,
        timestamp_tolerance_seconds: int = 300,
        nonce_ttl_seconds: int = 600,
    ) -> None:
        self.client_secrets = dict(client_secrets)
        self.nonce_store = nonce_store
        self.timestamp_tolerance_seconds = timestamp_tolerance_seconds
        self.nonce_ttl_seconds = nonce_ttl_seconds

    def authenticate(
        self,
        *,
        method: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> str:
        client_id = headers.get("X-SIMS-Client-Id")
        timestamp = headers.get("X-SIMS-Timestamp")
        nonce = headers.get("X-SIMS-Nonce")
        signature = headers.get("X-SIMS-Signature")
        if not all([client_id, timestamp, nonce, signature]):
            raise AuthenticationError("Missing authentication headers")

        secret = self.client_secrets.get(client_id)
        if secret is None:
            raise AuthenticationError("Unknown client")

        try:
            ts = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise AuthenticationError("Invalid timestamp") from exc
        if ts.tzinfo is None:
            raise AuthenticationError("Timestamp must include timezone")

        now = datetime.now(timezone.utc)
        delta = abs((now - ts.astimezone(timezone.utc)).total_seconds())
        if delta > self.timestamp_tolerance_seconds:
            raise AuthenticationError("Timestamp outside allowed tolerance")

        if not self.nonce_store.claim(
            client_id, nonce, ttl_seconds=self.nonce_ttl_seconds
        ):
            raise AuthenticationError("Replay detected")

        expected = self.sign(
            secret=secret,
            method=method,
            path=path,
            timestamp=timestamp,
            nonce=nonce,
            body=body,
        )
        if not hmac.compare_digest(expected, signature):
            raise AuthenticationError("Invalid signature")
        return client_id

    @staticmethod
    def sign(
        *,
        secret: str,
        method: str,
        path: str,
        timestamp: str,
        nonce: str,
        body: bytes,
    ) -> str:
        body_hash = hashlib.sha256(body).hexdigest()
        canonical = "\n".join([
            method.upper(),
            path,
            timestamp,
            nonce,
            body_hash,
        ]).encode("utf-8")
        return hmac.new(
            secret.encode("utf-8"),
            canonical,
            hashlib.sha256,
        ).hexdigest()
