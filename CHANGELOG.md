## 1.2.0-RC4

- Structured internal-link referral metadata and workflow scope propagation.


## 1.2.0-RC3
- Shared 3.5.0 Presentation Frameworkへ同期。
- Doctor結果へHuman-facing `presentation` projectionを追加。
- Machine ContractとHuman Outputを分離し、内部用語の通常表示を禁止。
# v1.1.3

- `workflow_handoff.next_action`を必須化。
- 次担当を機械可読でSBMへ返し、紹介状本文はSBMが生成。

# v1.1.2

- Restore required Doctor result JSON registration to SBM.
- Move final specialist referral generation to SBM.
- Remove direct specialist request from normal Doctor output.

# v1.1.1
- URL identity and canonical diagnostic accuracy update.
- Trailing-slash aliases no longer trigger false indexing-loss conclusions.

# CHANGELOG

## 1.0.3
- Direct specialist handoff: Doctor → Writer / Creator / Merge → SBM.
- Doctor result registration in SBM is optional archive only.

## [1.0.2] - 2026-08-07

- Corrected all current release and Claude deployment identity metadata to 1.0.2.
- Added release consistency checks for VERSION, identity, manifests, instructions, and deployment tests.

## v1.0.2
- Workflow handoff: treatment class, prioritized checklist, and specialist request texts.

# Changelog

## [1.0.1] - 2026-08-06

- Added action-first user output and SBM-routed handoff instructions.
- Kept diagnosis logic and machine-readable codes unchanged.


## [1.0.0-RC13] - 2026-08-05

- Added SIMS Editorial Platform v1 common envelope and Doctor diagnosis request/result schemas.
- Synchronized Doctor-scoped Shared snapshot to Shared Editorial Knowledge 3.3.0.
- Added product identity and explicit Shared version metadata.
- Preserved `SIMS_DOCTOR_CASE_RESULT_V2` as a legacy compatibility route.
- Formalized SBM-only treatment routing and prohibited direct Doctor-to-treatment-product invocation.
- Added RC13 platform contract adaptation documentation.

## 1.0.0-RC1 — 2026-08-04

- Finalized SIMS Doctor v1.0.0 release candidate
- Froze diagnostic and treatment-policy responsibilities
- Added release manifest, checklist, architecture freeze, and integrity tests
- Added repository release audit
- Did not add treatment execution

## 1.0.0-sprint10.3-explainable-diagnosis — 2026-08-04

- Added Explainable Diagnosis
- Added SIMS_DOCTOR_EXPLANATION_V1
- Added user-facing decision paths and system audit traces
- Added blocking and supporting factors
- Added Medical Record explanation history and tests

## 1.0.0-sprint10.2-doctor-report-generator — 2026-08-04

- Added user-facing and system-facing Doctor reports
- Added SIMS_DOCTOR_REPORT_V1
- Preserved DiagnosisReportBuilder compatibility
- Added Medical Record history and tests

## 1.0.0-sprint10.1-treatment-recommendation — 2026-08-04

- Added Treatment Recommendation Engine
- Added SIMS_DOCTOR_TREATMENT_RECOMMENDATION_V1
- Added Writer, Creator, Merge, Observe, Follow-Up, and None routing
- Added treatment scope, prohibited actions, priority, and monitoring
- Added Winner Query, full-rewrite, new-article, and Merge safeguards
- Added Referral Factory
- Added Writer request contract fixture
- Added Medical Record recommendation history
- Added TREATMENT_RECOMMENDATION_CREATED event
- Added contract, unit, integration, and regression tests
- Did not add treatment execution, publication, redirect, delete, or noindex

## 1.0.0-sprint10.0-composite-diagnosis — 2026-08-04

- Added Composite Diagnosis Engine
- Added SIMS_DOCTOR_COMPOSITE_DIAGNOSIS_V1
- Added weighted integration of specialist assessments
- Added Vital Score, Content Integrity, and Competition Resilience integration
- Added LOW_SAMPLE, recent-change, Winner Query, Merge, and role-separation safety precedence
- Added Healthy, Minor Refresh, Local Optimization, Full Rewrite, New Article, Merge, Observe, and Follow-Up outcomes
- Added confidence, priority, supporting-assessment, and trace output
- Added Medical Record composite diagnosis history
- Added COMPOSITE_DIAGNOSIS_COMPLETED event
- Added contract, unit, integration, and regression tests
- Did not add treatment execution or referral generation

## 1.0.0-sprint9.9-cannibalization-diagnosis — 2026-08-04

- Added Cannibalization Diagnosis
- Added Merge Candidate and Role Separation
- Added safety protections and Rule Engine integration
- Added tests

## 1.0.0-sprint9.8-freshness-decay-diagnosis — 2026-08-04

- Added Freshness Decay Diagnosis
- Added article-age and FRESHNESS Vital Sign integration
- Added outdated year, price, specification, procedure, policy, screenshot, and reference signals
- Added partial and severe freshness decay
- Added recent-update observation
- Added Winner Query protection and preferred update scope
- Added SIMS_DOCTOR_FRESHNESS_DECAY_ASSESSMENT_V1
- Added Freshness Decay rules to the Diagnostic Rule Engine
- Added Medical Record assessment history
- Added FRESHNESS_DECAY_ASSESSED event
- Added contract, unit, integration, and regression tests
- Did not add automatic fact verification, content updates, deletion, noindex, or SERP freshness comparison

## 1.0.0-sprint9.7-intent-drift-diagnosis — 2026-08-04

- Added Intent Drift Diagnosis
- Added query-cluster concentration and normalized entropy
- Added primary and secondary intent shares
- Added query-title overlap
- Added emerging-intent transition detection
- Added Winner Query protection and LOW_SAMPLE safeguards
- Added SIMS_DOCTOR_INTENT_DRIFT_ASSESSMENT_V1
- Added Intent Drift rules to the Diagnostic Rule Engine
- Added Medical Record assessment history
- Added INTENT_DRIFT_ASSESSED event
- Added contract, unit, integration, and regression tests
- Did not add automatic article creation, merge, deletion, semantic embeddings, or SERP intent classification

## 1.0.0-sprint9.6-position-opportunity-diagnosis — 2026-08-04

- Added Position Opportunity Diagnosis
- Added high, normal, and query-focused ranking opportunities
- Added Winner Query protection
- Added low-visibility or intent-misalignment signal
- Added Competition Resilience and Content Integrity integration
- Added LOW_SAMPLE safeguards
- Added SIMS_DOCTOR_POSITION_OPPORTUNITY_ASSESSMENT_V1
- Added Position Opportunity rules to the Diagnostic Rule Engine
- Added Medical Record assessment history
- Added POSITION_OPPORTUNITY_ASSESSED event
- Added contract, unit, integration, and regression tests
- Did not add automatic new article creation, deletion, or Writer execution

## 1.0.0-sprint9.5-ctr-opportunity-diagnosis — 2026-08-04

- Added CTR Opportunity Diagnosis
- Added Winner Query and recent-title-change safeguards
- Added Diagnostic Rule integration
- Added tests

## 1.0.0-sprint9.4-long-term-degradation-diagnosis — 2026-08-04

- Added Long-Term Degradation Diagnosis
- Added 365-day trend, Vital Score, recurrence, seasonality, and recovery integration
- Added chronic, sharp, CTR, and position degradation classifications
- Added seasonality and recovery safety gates
- Added LOW_SAMPLE confidence reduction
- Added SIMS_DOCTOR_LONG_TERM_DEGRADATION_ASSESSMENT_V1
- Added long-term degradation rules to the Diagnostic Rule Engine
- Added Medical Record assessment history
- Added LONG_TERM_DEGRADATION_ASSESSED event
- Added contract, unit, integration, and regression tests
- Did not add core-update calendar correlation, external seasonality data, or automatic Writer execution

## 1.0.0-sprint9.3-improvement-failure-diagnosis — 2026-08-04

- Added Improvement Failure Diagnosis
- Added treatment-history and Vital Score integration
- Added no-effect, worsening, wrong-direction, recurrent-failure, and insufficient-follow-up classifications
- Added LOW_SAMPLE safety behavior
- Added SIMS_DOCTOR_IMPROVEMENT_FAILURE_ASSESSMENT_V1
- Added Improvement Failure rules to the Diagnostic Rule Engine
- Added Medical Record assessment history
- Added IMPROVEMENT_FAILURE_ASSESSED event
- Added contract, unit, integration, and regression tests
- Did not add automatic rollback or automatic Writer execution

## 1.0.0-sprint9.2-vital-score-engine — 2026-08-04

- Added Vital Score Engine
- Added SIMS_DOCTOR_VITAL_SCORE_RESULT_V1
- Added weighted seven-sign article health score
- Added missing-sign reweighting and insufficient-data handling
- Added LOW_SAMPLE, severe-Finding, and critical-Finding penalties
- Added recovery bonus
- Added health bands and explainable positive and negative factors
- Added Medical Record Vital Score history
- Added VITAL_SCORE_CALCULATED event
- Added contract, unit, integration, and regression tests
- Did not replace individual Vital Signs or generate diagnosis and treatment directly

## 1.0.0-sprint9.1-diagnostic-rule-engine — 2026-08-04

- Added declarative Diagnostic Rule Engine
- Added diagnostic rule and evaluation-result contracts
- Added rule registry and validation
- Added Evidence, Finding, Vital Sign, Observation, Longitudinal, Treatment History, and Context sources
- Added deterministic ordering and explainable condition results
- Added confidence bonuses and low-sample penalties
- Added same-diagnosis and mutual-exclusion conflict resolution
- Added Medical Record rule-evaluation history
- Added DIAGNOSTIC_RULES_EVALUATED event
- Added contract, unit, integration, and regression tests
- Did not replace Differential Diagnosis or generate treatment and referrals directly

## 1.0.0-sprint8.6-production-security-deployment — 2026-08-04

- Added SQLite-persistent nonce replay protection
- Added SQLite-persistent API idempotency storage
- Added SQLite audit logging
- Added environment-based client secret configuration
- Added invalid and placeholder secret rejection
- Added production application factory
- Added liveness and readiness endpoints
- Added queue and security database readiness checks
- Added production operations documentation
- Added unit, integration, and regression tests
- Did not add TLS, cloud secret manager, managed database, multi-worker rate limiting, or public deployment

## 1.0.0-sprint8.5-transport-api-auth — 2026-08-04

- Added SBM–Doctor transport API
- Added batch submit, status, and result endpoints
- Added HMAC-SHA256 request authentication
- Added timestamp and nonce replay protection
- Added per-client rate limiting
- Added Idempotency-Key support
- Added audit logging
- Added WSGI adapter
- Added unit, integration, and regression tests
- Did not add TLS termination, production secret management, OAuth, or public deployment configuration

## 1.0.0-sprint8.4-sbm-batch-integration — 2026-08-04

- Added SBM-to-Doctor batch request contract
- Added accepted and progress status contracts
- Added terminal result package contract
- Added idempotent import acknowledgement contract
- Added SBM Batch Gateway
- Added duplicate batch submission detection
- Added safe status projection without internal request payloads or error messages
- Added result fingerprinting
- Added SQLite SBM import ledger and duplicate import prevention
- Added Apps Script lightweight contract validators
- Added contract, unit, integration, and regression tests
- Did not add SBM UI, HTTP transport, authentication, automatic polling, or Medical Record export

## 1.0.0-sprint8.3-production-queue-scheduler — 2026-08-04

- Added SQLite durable Batch Queue adapter
- Added WAL, synchronous transactions, and busy timeout
- Added persistence across process restart
- Added Scheduler CLI for enqueue, run, status, and incomplete-list operations
- Added pluggable module:function executor loading
- Added JSONL operations logging and automation exit codes
- Added repository, restart, CLI, and regression tests
- Did not add cloud database, cron installation, parallel workers, SBM UI, or external notifications

## 1.0.0-sprint8.2-persistent-batch-queue — 2026-08-04

- Added storage-neutral persistent Batch Queue
- Added queue record contract
- Added idempotent enqueue
- Added lease-based worker locking and expired-lock recovery
- Added item-level durable checkpoints
- Added retry scheduling with backoff
- Added pause and resume
- Added Nightly Batch Worker cycle
- Added incomplete-batch discovery and lifecycle events
- Added contract, unit, integration, and regression tests
- Did not add production database, cron deployment, parallel workers, external notifications, or SBM batch UI

## 1.0.0-sprint8.1-batch-doctor-foundation — 2026-08-04

- Added Batch Doctor request and result contracts
- Added per-article Case isolation
- Added longitudinal, severity, recurrence, and traffic-opportunity priority scoring
- Added priority-ordered batch execution
- Added continue-after-case-failure behavior
- Added resume and retry-limit foundation
- Added aggregate Writer, Creator, Merge, and follow-up counts
- Added contract, unit, integration, and regression tests
- Did not add persistent queues, scheduling, parallel workers, or SBM batch UI

## 1.0.0-sprint7.4-longitudinal-medical-record — 2026-08-04

- Added Longitudinal Medical Record Analysis
- Added repeated diagnosis, dominant diagnosis, and recurrence counting
- Added chronic-case detection
- Added treatment responsiveness and resistance analysis
- Added repeated defer-pattern and recent-recurrence detection
- Added follow-up priority
- Added SIMS_DOCTOR_LONGITUDINAL_PROFILE_V1
- Added LONGITUDINAL_PROFILE_UPDATED event and Medical Record profile history
- Added contract, unit, integration, and regression tests
- Did not add batch diagnosis, scheduling, cross-site aggregation, or automatic treatment

## 1.0.0-sprint7.3-improvement-history — 2026-08-04

- Added Improvement History Comparison
- Added baseline and post-treatment checkpoint analysis
- Added weighted clicks, impressions, CTR, and position effect score
- Added improvement, no-effect, worsening, mixed-response, and insufficient-follow-up classifications
- Added treatment-response Evidence and Findings
- Added TREATMENT_SUCCESS, IMPROVEMENT_FAILURE, POST_IMPROVEMENT_WORSENING, MIXED_TREATMENT_RESPONSE, and FOLLOW_UP_REQUIRED diagnoses
- Added Writer review for ineffective or worsening treatment
- Added Observation routing for success and follow-up cases
- Added contract, unit, integration, and regression tests
- Did not add automatic rollback or article restoration

## 1.0.0-sprint7.2-long-term-decline — 2026-08-04

- Added long-term 365-day window analysis
- Added gradual decline, sharp decline, CTR decay, position decay, seasonality, and recovery classification
- Added Long-Term Observation contract
- Added long-term Evidence and Findings engines
- Added LONG_TERM_DECAY, SEASONAL_DECLINE, and RECOVERY_IN_PROGRESS diagnoses
- Added Writer and Observation routing
- Added contract, unit, integration, and regression tests
- Did not add core-update calendar correlation, external seasonality data, or batch diagnosis

## 1.0.0-sprint7.1-cross-article-cannibalization — 2026-08-04

- Added Cross-Article Observation contract and analyzer
- Added shared-query, title-similarity, and intent-similarity evaluation
- Added Cannibalization, Merge Candidate, and New Article Opportunity findings
- Added CANNIBALIZATION, ARTICLE_MERGE_REQUIRED, and NEW_ARTICLE_NEEDED diagnoses
- Activated Merge and Creator routing
- Added Cross-Article Findings Engine
- Added contract, unit, integration, and regression tests
- Did not add actual merge, creation, deletion, noindex, or batch diagnosis execution

## 1.0.0-sprint6.5-diagnosis-report-output — 2026-08-04

- Added user-facing Japanese Diagnosis Report
- Added SIMS_DOCTOR_SINGLE_CASE_RESULT_V1
- Added SIMS_DOCTOR_WRITER_REQUEST_V1
- Added Writer treatment goals and preservation constraints
- Added confirmed and deferred output handling
- Added OUTPUT_GENERATED event
- Added Medical Record output history and counters
- Added contract, unit, integration, and regression tests
- Did not add Creator, Merge, SBM import, or graphical UI implementations

## 1.0.0-sprint6.4-clinical-pipeline — 2026-08-04

- Added Clinical Pipeline Orchestrator
- Added end-to-end coordination from Observation through Referral
- Added partial Observation failure tolerance
- Added stop-on-clinical-step failure
- Added idempotent replay and resume foundation
- Added CLINICAL_PIPELINE_COMPLETED event
- Added SIMS_DOCTOR_CLINICAL_PIPELINE_RESULT_V1
- Added Medical Record pipeline history and counters
- Added unit and integration tests
- Did not add persistent queueing, scheduling, credentials, or user-facing report rendering

## 1.0.0-sprint6.3-article-snapshot — 2026-08-04

- Added SIMS_DOCTOR_ARTICLE_SNAPSHOT_INPUT_V1
- Added Article Snapshot models and Medical Record integration
- Added title, headings, FAQ, internal links, metrics, and freshness observations
- Added previous-snapshot structural comparison
- Enabled Content Integrity Vital Sign
- Completed availability path for all seven Vital Signs
- Added contract, unit, integration, and regression tests
- Did not add live crawling, CMS-specific parsing, or content editing

## 1.0.0-sprint6.2-serp-observation — 2026-08-04

- Added provider-neutral SERP acquisition interface
- Added SIMS_DOCTOR_SERP_OBSERVATION_INPUT_V1
- Added intent inference and SERP feature recording
- Added normalized competition metrics
- Added previous SERP comparison
- Added SERP Medical Record Observation integration
- Enabled Competition Resilience Vital Sign
- Added contract, unit, and integration tests
- Did not add provider credentials, browser scraping, or Article Snapshot Observation

## 1.0.0-sprint6.1-search-console-acquisition — 2026-08-04

- Added provider-neutral Search Console acquisition interface
- Added Google Search Console API adapter
- Added 28, 90, and 365-day aggregate retrieval
- Added query-level paging and policy limits
- Added retry for transient provider errors
- Added COMPLETE, PARTIAL, FAILED, and NO_DATA acquisition states
- Added conversion to SIMS_DOCTOR_SEARCH_CONSOLE_OBSERVATION_INPUT_V1
- Added unit and end-to-end Observation integration tests
- Did not add credential storage, OAuth UI, scheduling, or SERP acquisition

## 1.0.0-sprint5.1-treatment-referral — 2026-08-04

- Added Treatment Recommendation Engine
- Added Referral Routing Engine
- Preserved separation between diagnosis, treatment recommendation, and referral
- Added Writer routing for confirmed diagnoses
- Added Observation routing for deferred diagnoses
- Added TREATMENT_RECOMMENDED and REFERRAL_ISSUED events
- Added SIMS_DOCTOR_REFERRAL_V1 schema
- Extended Medical Record counters
- Added unit and integration tests
- Reserved Creator, Merge, noindex, and delete routing for later diagnosis expansion

## 1.0.0-sprint4.3-final-diagnosis — 2026-08-04

- Added Diagnosis Validation and Final Diagnosis Engine
- Added CONFIRMED and DEFERRED outcomes
- Added review dates and event logging

## 1.0.0-sprint4.2-differential-diagnosis — 2026-08-04

- Added Differential Diagnosis Engine
- Added versioned Diagnosis Code Registry
- Added supporting and contradicting Finding rules
- Added confidence scoring, ranking, and low-sample penalty
- Added context-sensitive UPDATE_FAILURE candidate
- Added idempotent DIFFERENTIAL_UPDATED event
- Extended Medical Record schema and counters
- Added unit and integration tests
- Did not add Final Diagnosis, treatment, or referral generation

## 1.0.0-sprint4.1-findings-engine — 2026-08-04

- Added Findings Engine foundation
- Added versioned Finding rules to CKB
- Added severity and confidence calculation
- Linked every Finding to Evidence and Vital Profile
- Added LOW_SAMPLE confidence penalty
- Added deterministic Finding fingerprint and duplicate prevention
- Added FINDING_RECORDED event
- Extended Medical Record schema and counters
- Added unit and integration tests
- Did not add Differential or Final Diagnosis

## 1.0.0-sprint3.4-vital-signs-profile — 2026-08-04

- Added Vital Signs Engine
- Added seven-sign Vital Profile
- Added versioned formula registry to CKB
- Implemented Visibility, Traffic, CTR Health, Ranking Stability, and Freshness
- Marked Competition Resilience and Content Integrity as UNAVAILABLE pending observations
- Added normal-range classification and overall profile score
- Added LOW_SAMPLE confidence and score adjustments
- Added idempotent VITAL_SIGNS_CALCULATED event
- Extended Medical Record schema and counters
- Added unit and integration tests
- Did not add Findings or Diagnosis

## 1.0.0-sprint3.3-evidence-engine — 2026-08-04

- Added Evidence Engine foundation
- Added four initial Evidence extraction rules
- Added versioned Evidence thresholds and sample policy to CKB
- Added LOW_SAMPLE retention and flagging
- Added Evidence IDs, Observation linkage, measured values, and comparison basis
- Added deterministic Evidence fingerprint and duplicate prevention
- Added EVIDENCE_RECORDED Medical Record events
- Extended Medical Record schema and counters
- Added unit and integration tests
- Did not add Vital Signs, Findings, or Diagnosis

## 1.0.0-sprint3.2-observation-event-log — 2026-08-04

- Added append-only Medical Record Event Log
- Added sequence, idempotency, and SHA-256 payload integrity checks
- Added Search Console 28/90/365-day Observation input contract
- Added retrieval states COMPLETE, PARTIAL, FAILED, and NO_DATA
- Added Search Console domain models and Observation recording service
- Added Medical Record schema support for events and typed observations
- Added unit, integration, and contract tests
- Did not add live Search Console API retrieval or diagnostic evaluation

## 1.0.0-sprint3.1-ckb — 2026-08-04

- Added Clinical Knowledge Base v1.0
- Added Observation, Evidence, Vital Signs, Findings, and event registries
- Standardized all Vital Signs as “higher is healthier”
- Added normal-range classifications from NORMAL to SEVERE
- Added CKB loader and structural validation
- Added immutable clinical data model foundations
- Added CKB and observation model tests
- Kept diagnosis, scoring formulas, and referrals out of Sprint3.1

# Changelog

## [1.0.1] - 2026-08-06

- Added action-first user output and SBM-routed handoff instructions.
- Kept diagnosis logic and machine-readable codes unchanged.


## 1.0.0-sprint2.2-foundation — 2026-08-04

- Added Request Receiver, validator and normalizer
- Added Request ID and Case ID generation
- Added active-case reuse by site and article identity
- Added Case Registry and Medical Record reference repositories
- Added initial medical-record generation and request history append
- Added acceptance/rejection result generation
- Added unit and integration tests
- Preserved existing catalog importer, contracts and SBM safety boundary

## 1.0.0-sprint2.1-design — 2026-08-04

- Added provisional JSON Schemas for the four approved Doctor contracts
- Added Case Lifecycle v1
- Added valid and invalid contract fixtures
- Added fixture validation script
- Added SBM compatibility checklist

## 1.0.0-RC4 - 2026-08-05
- Added Clinical Review and limited factual repair.
- Split evidence acquisition quality from content quality.
- Added factor-based confidence scoring and external demand diagnosis.
- Added multi-track treatment and Japanese user-facing output policy.

## 1.0.4
- Hide Doctor diagnosis JSON from normal user-facing responses.
- Require a standalone copy-ready request block for Writer, Creator, or Merge.
- Clarify that only specialist treatment results return to SBM.

## 1.1.0 - Treatment Plan UX
- Added reassurance, concrete ToDo, do-not-do guidance, confidence-led decisions, and copy-ready specialist handoff.
