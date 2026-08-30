# Sprint8.5 — SBM–Doctor Transport API and Authentication Foundation

## Included

- transport API application layer
- HMAC-SHA256 request authentication
- timestamp and nonce replay protection
- per-client rate limiting
- submission idempotency keys
- batch submit, status, and result endpoints
- audit log
- WSGI adapter
- unit, integration, and regression tests

## Excluded

- TLS termination
- production secret manager
- OAuth
- public internet deployment
- reverse proxy configuration
- SBM-side network client implementation
