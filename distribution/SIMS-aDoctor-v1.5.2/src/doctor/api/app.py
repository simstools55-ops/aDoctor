from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Mapping

from src.doctor.integration.sbm import SbmBatchGateway, SbmIntegrationError
from src.doctor.security import (
    AuthenticationError, HmacAuthenticator,
    InMemoryRateLimiter, RateLimitError,
)
from .audit import InMemoryAuditLog
from .idempotency import InMemoryIdempotencyStore


@dataclass(frozen=True)
class ApiResponse:
    status_code: int
    body: dict[str, Any]
    headers: dict[str, str]


class DoctorApiApp:
    def __init__(
        self,
        *,
        gateway: SbmBatchGateway,
        authenticator: HmacAuthenticator,
        rate_limiter: InMemoryRateLimiter,
        idempotency_store: InMemoryIdempotencyStore,
        audit_log: InMemoryAuditLog,
        idempotency_ttl_hours: int = 24,
    ) -> None:
        self.gateway = gateway
        self.authenticator = authenticator
        self.rate_limiter = rate_limiter
        self.idempotency_store = idempotency_store
        self.audit_log = audit_log
        self.idempotency_ttl_hours = idempotency_ttl_hours
        self.readiness_checks: list[callable] = []

    def handle(
        self,
        *,
        method: str,
        path: str,
        headers: Mapping[str, str],
        body: bytes = b"",
    ) -> ApiResponse:
        client_id = None
        request_id = headers.get("X-Request-Id")
        try:
            client_id = self.authenticator.authenticate(
                method=method,
                path=path,
                headers=headers,
                body=body,
            )
            self.rate_limiter.check(client_id)

            if method.upper() == "GET" and path == "/health/live":
                response = ApiResponse(200, {"status": "LIVE"}, {})
            elif method.upper() == "GET" and path == "/health/ready":
                ready = all(check() for check in self.readiness_checks)
                response = ApiResponse(
                    200 if ready else 503,
                    {"status": "READY" if ready else "NOT_READY"},
                    {},
                )
            elif method.upper() == "POST" and path == "/v1/sbm/batches":
                response = self._submit(client_id, headers, body)
            else:
                match = re.fullmatch(r"/v1/sbm/batches/([^/]+)(/result)?", path)
                if method.upper() == "GET" and match:
                    queue_id = match.group(1)
                    response = (
                        self._result(queue_id)
                        if match.group(2)
                        else self._status(queue_id)
                    )
                else:
                    response = ApiResponse(
                        404,
                        {"error": {"code": "NOT_FOUND", "message": "Endpoint not found"}},
                        {},
                    )

            self.audit_log.append(
                client_id=client_id,
                method=method,
                path=path,
                status_code=response.status_code,
                event="API_REQUEST_COMPLETED",
                request_id=request_id,
            )
            return response
        except AuthenticationError as exc:
            return self._error(
                401, "AUTHENTICATION_FAILED", str(exc),
                client_id, method, path, request_id
            )
        except RateLimitError as exc:
            return self._error(
                429, "RATE_LIMITED", str(exc),
                client_id, method, path, request_id
            )
        except (SbmIntegrationError, ValueError, json.JSONDecodeError) as exc:
            return self._error(
                400, "INVALID_REQUEST", str(exc),
                client_id, method, path, request_id
            )
        except Exception:
            return self._error(
                500, "INTERNAL_ERROR", "Internal server error",
                client_id, method, path, request_id
            )

    def _submit(
        self,
        client_id: str,
        headers: Mapping[str, str],
        body: bytes,
    ) -> ApiResponse:
        key = headers.get("Idempotency-Key")
        if not key:
            raise ValueError("Idempotency-Key header is required")
        existing = self.idempotency_store.get(client_id, key)
        if existing:
            return ApiResponse(200, existing, {"Idempotent-Replay": "true"})

        payload = json.loads(body.decode("utf-8"))
        accepted = self.gateway.submit(payload)
        self.idempotency_store.put(
            client_id,
            key,
            accepted,
            ttl_hours=self.idempotency_ttl_hours,
        )
        return ApiResponse(202, accepted, {})

    def _status(self, queue_id: str) -> ApiResponse:
        return ApiResponse(200, self.gateway.status(queue_id), {})

    def _result(self, queue_id: str) -> ApiResponse:
        return ApiResponse(200, self.gateway.export_result(queue_id), {})

    def _error(
        self,
        status_code: int,
        code: str,
        message: str,
        client_id: str | None,
        method: str,
        path: str,
        request_id: str | None,
    ) -> ApiResponse:
        self.audit_log.append(
            client_id=client_id,
            method=method,
            path=path,
            status_code=status_code,
            event=code,
            request_id=request_id,
        )
        return ApiResponse(
            status_code,
            {"error": {"code": code, "message": message}},
            {},
        )
