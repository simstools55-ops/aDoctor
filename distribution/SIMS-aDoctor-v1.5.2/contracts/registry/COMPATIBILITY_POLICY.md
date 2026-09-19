# Compatibility Policy v0.1.0

- `contract_version`: breaking contract generation, `MAJOR.MINOR`.
- `schema_version`: structural revision, `MAJOR.MINOR.PATCH`.
- Optional field additions are backward compatible.
- Required field additions, type changes, removals, and semantic changes require a new major contract version.
- Receivers must ignore unknown optional fields.
- Receivers must reject unsupported contract versions explicitly.
- Duplicate `message_id` must not create duplicate records or locks.
