# Platform Contract Adaptation RC13

SIMS Article Doctor RC13 adopts Shared Editorial Knowledge 3.3.0.

## Canonical path

- Input: `SIMS_DOCTOR_DIAGNOSIS_REQUEST_V1`
- Output: `SIMS_DOCTOR_DIAGNOSIS_RESULT_V1`
- Follow-up: referrals are returned to SBM only.
- Re-examination remains SBM -> Doctor -> SBM.

## Compatibility

`SIMS_DOCTOR_CASE_RESULT_V2` remains readable and can be normalized by the SBM adapter. Doctor does not invoke Writer, Creator, or Merge directly.

## Identity ownership

SBM owns SiteID, ArticleID, CaseID and workflow state. Doctor owns diagnosis_id and diagnostic evidence records.
