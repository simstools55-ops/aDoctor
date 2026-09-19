# Reception Foundation Architecture

```text
SBM JSON
  -> Request Receiver
  -> Validator
  -> Normalizer
  -> Active Case Lookup
  -> Case Registry + Medical Record transaction
  -> SIMS_DOCTOR_SINGLE_CASE_RESULT_V1
```

The in-memory repositories are reference adapters for Sprint2-2. Production persistence must preserve the same interfaces and atomicity rules.

Raw and normalized requests are separated at the receiver boundary. Diagnosis components must never depend on the raw SBM request.
