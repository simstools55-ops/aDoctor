# SBM–Doctor Transport API

## Endpoints

- `POST /v1/sbm/batches`
- `GET /v1/sbm/batches/{queue_record_id}`
- `GET /v1/sbm/batches/{queue_record_id}/result`

## Authentication

Requests use `SIMS-HMAC-SHA256`.

The signature covers:

- HTTP method
- path
- timestamp
- nonce
- SHA-256 body hash

A timestamp tolerance and one-time nonce prevent replay.

## Idempotency

Batch submission requires `Idempotency-Key`.
The same client and key return the original accepted response.

## Security boundaries

The API never returns Medical Records, internal Findings, raw Evidence, or tracebacks.
