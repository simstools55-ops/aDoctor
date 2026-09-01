# SIMS Article Doctor v1.0.0-RC1 Release Checklist

## Architecture
- [x] SBM and Doctor responsibilities remain separated
- [x] Doctor Medical Record remains the diagnostic SSOT
- [x] JSON contracts remain the system interface
- [x] Diagnosis and referral remain separated
- [x] Doctor does not execute treatment

## Diagnostic workflow
- [x] Request reception and Case creation
- [x] Medical Record creation
- [x] 365-day data architecture
- [x] Evidence, Observation, Finding, Vital Sign
- [x] Specialist diagnosis engines
- [x] Cannibalization diagnosis
- [x] Composite Diagnosis
- [x] Treatment Recommendation
- [x] Doctor Report
- [x] Explainable Diagnosis

## Safety
- [x] LOW_SAMPLE safeguard
- [x] Winner Query protection
- [x] Recent-change observation
- [x] No automatic delete, noindex, redirect, publication, or merge execution

## Quality
- [x] Contract fixture validation
- [x] Unit, integration, regression, and release tests
- [x] JSON syntax validation
- [x] UTF-8 text validation
- [x] SHA256 manifest
