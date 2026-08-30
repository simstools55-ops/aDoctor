from __future__ import annotations

from src.doctor.api import DoctorApiApp
from src.doctor.api.wsgi import create_wsgi_app
from src.doctor.batch import BatchPriorityCalculator
from src.doctor.batch.queue import BatchQueueService
from src.doctor.batch.queue.sqlite_repository import SQLiteBatchQueueRepository
from src.doctor.config import DoctorSettings
from src.doctor.integration.sbm import SbmBatchGateway
from src.doctor.knowledge import ClinicalKnowledgeBase
from src.doctor.security import (
    HmacAuthenticator,
    InMemoryRateLimiter,
    SQLiteAuditLog,
    SQLiteIdempotencyStore,
    SQLiteNonceStore,
    SQLiteSecurityState,
)


def create_api(settings: DoctorSettings | None = None) -> DoctorApiApp:
    settings = settings or DoctorSettings.from_environment()
    knowledge = ClinicalKnowledgeBase(settings.repository_root / "knowledge").load()
    queue_policy = knowledge.batch_queue_policy()
    batch_policy = knowledge.batch_policy()
    transport_policy = knowledge.transport_api_policy()

    queue_repository = SQLiteBatchQueueRepository(settings.queue_database)
    queue_service = BatchQueueService(
        repository=queue_repository,
        policy=queue_policy,
        priority_calculator=BatchPriorityCalculator(batch_policy),
    )
    security_state = SQLiteSecurityState(settings.security_database)
    auth_policy = transport_policy["authentication"]

    api = DoctorApiApp(
        gateway=SbmBatchGateway(queue_service),
        authenticator=HmacAuthenticator(
            client_secrets=settings.client_secrets,
            nonce_store=SQLiteNonceStore(security_state),
            timestamp_tolerance_seconds=auth_policy["timestamp_tolerance_seconds"],
            nonce_ttl_seconds=auth_policy["nonce_ttl_seconds"],
        ),
        rate_limiter=InMemoryRateLimiter(
            requests_per_minute=settings.requests_per_minute,
            burst=settings.burst,
        ),
        idempotency_store=SQLiteIdempotencyStore(security_state),
        audit_log=SQLiteAuditLog(security_state),
        idempotency_ttl_hours=transport_policy["idempotency"]["ttl_hours"],
    )
    api.readiness_checks = [
        lambda: queue_repository.ping(),
        lambda: security_state.ping(),
        lambda: bool(settings.client_secrets),
    ]
    return api


def create_application(settings: DoctorSettings | None = None):
    return create_wsgi_app(create_api(settings))
