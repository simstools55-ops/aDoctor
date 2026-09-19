# Production Deployment Foundation

## Required environment variables

```text
SIMS_DOCTOR_REPOSITORY_ROOT
SIMS_DOCTOR_QUEUE_DB
SIMS_DOCTOR_SECURITY_DB
SIMS_DOCTOR_CLIENT_SECRETS_JSON
```

`SIMS_DOCTOR_CLIENT_SECRETS_JSON` example:

```json
{"sbm":"replace-with-a-random-secret-of-at-least-16-characters"}
```

Do not commit real secrets to Git.

## WSGI factory

```text
src.doctor.deployment.app_factory:create_application
```

## Health endpoints

```text
GET /health/live
GET /health/ready
```

## Worker recommendation

Use one API process while SQLite is the production store. Multiple processes should wait
until queue, nonce, idempotency, and rate-limit state use a shared external database.
