# SBM Compatibility Checklist

Use one JSON copied from the current SBM Doctor dialog.

1. Confirm exact top-level field names.
2. Confirm `contract_version`.
3. Confirm site identity field names.
4. Confirm article identity field names.
5. Confirm source screen values.
6. Confirm whether metrics and improvement history are included.
7. Confirm whether extra fields must be accepted.
8. Update only the provisional schema; do not change the SBM output without a contract revision.
9. Add the real JSON to `tests/fixtures/valid/`.
10. Run `python tests/contract/validate_fixtures.py`.
