# Vital Score Engine

Vital Score combines the latest seven Vital Signs into a single health indicator.

## Design

- each Vital Sign remains 0–100
- weights are policy-controlled
- missing signs are reweighted, not scored as zero
- fewer than three available signs returns `INSUFFICIENT_DATA`
- LOW_SAMPLE and serious Findings adjust the base score
- recovery Findings may add a limited bonus

## Boundary

Vital Score is a prioritization and explanation aid.
It does not replace Findings, diagnosis, or treatment decisions.
