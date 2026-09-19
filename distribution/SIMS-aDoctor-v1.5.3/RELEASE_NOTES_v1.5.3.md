# SIMS aDoctor v1.5.3

- Aligns the Claude operational request gate with the existing `SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2` Manager contract.
- Removes the redundant requirement for a separate `SIMS-A/1` `[SIMS_REQUEST]` envelope.
- Requires V2 source/target identity and non-empty RequestID, CaseID, SiteID and ArticleID before normal diagnosis execution.
- Free-form direct diagnosis remains blocked.
- Diagnostic logic and Shared Editorial Knowledge 3.5.0 are unchanged.
