# Treatment Recommendation Engine

The engine converts Composite Diagnosis into a referral.

## Targets

- SIMS Writer
- SIMS Creator
- SIMS Merge
- Observe
- Follow-Up
- None

## Separation

- Composite Diagnosis decides what is wrong.
- Treatment Recommendation decides where the case should go.
- Referral Factory creates the target-specific request.
- Doctor never performs treatment.
