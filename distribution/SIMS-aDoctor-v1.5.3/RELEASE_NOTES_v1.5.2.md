# SIMS aDoctor v1.5.2-dev

- Added SIMS Request Protocol v1 as the canonical Manager-to-aDoctor request-entry specification.
- Normal aDoctor execution requires the `SIMS-A/1` Manager envelope for FULL edition requests.
- Invalid or direct free-form diagnostic requests must stop before diagnosis, Web/SERP research, treatment planning, or result JSON generation.
- Clarified that the protocol is operational prompt/workflow control, not License Center authentication or cryptographic authentication.
- Existing diagnosis logic, Shared Editorial Knowledge 3.5.0, and Doctor result contracts are unchanged.
