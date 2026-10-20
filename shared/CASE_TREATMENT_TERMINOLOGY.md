# Case and Treatment Terminology

- **Case**: One diagnosis-treatment-measurement-re-examination cycle concerning one article or an explicitly defined article group.
- **Treatment**: One concrete editorial action performed within a Case.
- **Referral**: Doctor's structured recommendation returned to SBM describing the destination, objective, allowed scope, blocked scope, and review conditions.
- **Treatment Plan**: Doctor's recommendation about whether treatment is needed, its level, priority, expected impact, risk, and review timing.
- **CaseID**: Issued and owned by SBM before diagnosis is requested.
- **DiagnosisID**: Issued by Doctor for each diagnosis result and stored under the SBM Case.
- **Treatment Request ID**: Issued by SBM when a treatment request is created.
- **Treatment Result ID**: Issued by Writer, Creator, or Merge for the returned result and stored by SBM.

## Product roles

- SBM owns Case state, routing, records, publication management, measurement, and re-examination scheduling.
- Doctor diagnoses, prepares the Treatment Plan and Referral, and performs re-examination when requested.
- Writer treats existing articles.
- Creator creates new articles.
- Merge will perform article consolidation when implemented.

Doctor does not directly dispatch a Treatment to a specialist product. SBM converts an accepted Referral into a specialist request.

`DELETE`, `NOINDEX`, `ARCHIVE`, and `MERGE` are Treatments or disposition options, not diagnoses.
