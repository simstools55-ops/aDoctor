# SBM Safety Boundary

1. Doctor does not invoke SBM daily-processing functions.
2. SBM may reject Doctor request generation or treatment start while daily processing is active.
3. Doctor does not directly update SBM's article master, improvement history, Case state, or monitoring records.
4. SBM changes state only after validating an accepted platform message or a user action.
5. Doctor-specific time triggers and Properties keys use the `Doctor` prefix.
6. Doctor failure does not change SBM daily-processing state.
7. Doctor does not invoke Writer, Creator, or Merge directly.
8. Specialist treatment results return to SBM, not to Doctor.
9. Doctor cannot release or bypass an SBM Workflow Lock.
10. Re-examination is initiated by a new SBM request containing the relevant Case evidence.
