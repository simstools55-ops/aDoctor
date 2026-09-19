# Clinical Knowledge Base Architecture

The CKB is a versioned, declarative knowledge layer.

## Why JSON and Markdown coexist

- JSON registries are loaded and validated by Runtime.
- Markdown explains intent, governance, and interpretation to maintainers.
- Runtime must not parse prose to make production decisions.

## Change policy

- Additive code changes may remain in CKB v1.0.
- Meaning changes, threshold changes with behavioral impact, removals, and renames require version review.
- Unknown codes are rejected instead of guessed.
- Formulas remain `PENDING_CALIBRATION` until tested against real cases.

## Direction rule

Every health score uses “higher is healthier”.
This is why the competition Vital Sign is `COMPETITION_RESILIENCE`, not
`COMPETITION_PRESSURE`.
