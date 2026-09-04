# aDoctor v1.5.1

## Current release

`1.5.1`

### v1.5.1

- LOW_SAMPLE + structurally hard SERP now triggers `CLUSTER_OPPORTUNITY_CHECK` before low-priority closure.
- Added existing-content support and aCreator opportunity routes.
- New articles must have independent search intent/user value and pass cannibalization/SERP checks; thin link-only satellites are prohibited.
- Enforced workflow consistency: normal-close outcomes cannot simultaneously request WAIT/MONITOR.

## v1.0.4
- Workflow handoff: treatment class, prioritized checklist, and specialist request texts.

# aDoctor

Current user workflow: SIMS Manager → aDoctor → SIMS Manager → aWriter / aCreator / aMerge → SIMS Manager. Doctor JSON is internal and is not displayed to normal users; copy-ready specialist requests are shown instead. v1.0

aDoctor is the single-article precision diagnosis product in the SIMS Editorial Platform.
It receives a case request from SIMS Manager, maintains the medical record as the diagnostic SSOT, and later produces diagnosis and referral contracts. It does not rewrite articles.

## Current release

`1.1.3`

Sprint2-2 implements the reception foundation:

1. Receive `SIMS_DOCTOR_SINGLE_CASE_REQUEST_V1`
2. Validate and normalize the request
3. Generate Request ID
4. Create or reuse an active Case
5. Create or update `SIMS_DOCTOR_MEDICAL_RECORD_V1`
6. Return `SIMS_DOCTOR_SINGLE_CASE_RESULT_V1`

365-day data collection, SERP comparison, diagnosis, and referral generation remain outside this release.


## RC13 Platform Contract adaptation

RC13 synchronizes with SIMS Shared Editorial Knowledge 3.3.0 and adds the canonical Platform contracts `SIMS_DOCTOR_DIAGNOSIS_REQUEST_V1` and `SIMS_DOCTOR_DIAGNOSIS_RESULT_V1`. The existing `SIMS_DOCTOR_CASE_RESULT_V2` path remains supported as a legacy compatibility route. Doctor returns treatment referrals to SBM and never invokes Writer, Creator, or Merge directly.

## RC12 SBM orchestration

RC12 accepts SBM Evidence Package V2 requests, preserves SBM-issued CaseID, and returns `SIMS_DOCTOR_CASE_RESULT_V2` to SBM. Treatment execution is orchestrated by SBM; direct Doctor-to-Writer/Creator/Merge invocation is deprecated.

## Repository structure

```text
contracts/   JSON interface contracts and registries
docs/        architecture and compatibility documentation
integration/ SBM safety boundary documents
knowledge/   Doctor-specific diagnostic knowledge
product/     product definition and sprint specifications
runtime/     existing runtime assets and validators
src/doctor/  Sprint2-2 implementation
tests/       unit, contract and integration tests
```

## Run tests

```bash
python -m pip install pytest jsonschema
pytest -q
python tests/contract/validate_fixtures.py
```

## Compatibility warning

The single-case schemas remain provisional until compared with one real JSON copied from the current SBM Doctor dialog. Do not change SBM output silently to fit the schema. Contract incompatibility requires an explicit contract revision.

## Architectural principles

- SBM contains no Doctor diagnosis logic.
- JSON contracts are the only system-to-system interface.
- SBM owns the platform Case lifecycle; the Medical Record remains Doctor's diagnostic record.
- User-facing messages and system-facing contracts are separated.
- Diagnosis and referral are separate artifacts.
- Observation and diagnosis do not read the raw SBM request directly.


## Sprint3.1 Clinical Knowledge Base

Doctor now includes a declarative Clinical Knowledge Base for:

- Observation types
- Evidence codes
- Vital Signs and normal ranges
- Findings and severity
- Medical-record event types

Runtime loading is implemented in `src/doctor/knowledge/`.
Scoring, diagnosis, and referral decisions remain intentionally unimplemented.


## Sprint3.2 Observation Event Log

- Append-only Medical Record event log
- Event sequencing and payload-integrity verification
- Idempotent Observation replay
- 28/90/365-day Search Console input contract
- Search Console Observation recording into the medical record

Live Search Console retrieval remains outside this release.


## Sprint3.3 Evidence Engine

Doctor can now extract and store traceable Evidence from Observation data.

Initial Evidence codes:

- CTR_BELOW_POSITION_EXPECTATION
- POSITION_DECLINE_OBSERVED
- VISIBILITY_DECLINE_OBSERVED
- LONG_TIME_SINCE_UPDATE

Thresholds remain versioned in the Clinical Knowledge Base.
LOW_SAMPLE Evidence is retained and flagged.


## Sprint3.4 Vital Signs and Vital Profile

Doctor now creates a seven-sign Vital Profile.

Available now:

- Visibility
- Traffic
- CTR Health
- Ranking Stability
- Freshness

Unavailable until later Observation layers:

- Competition Resilience
- Content Integrity


## Sprint4.1 Findings Engine

Doctor now creates severity-bearing Findings from Evidence and the latest Vital Profile.

Initial Findings:

- CTR_UNDERPERFORMING
- POSITION_DECLINING
- LOW_VISIBILITY
- CONTENT_OUTDATED
- HIGH_VISIBILITY_LOW_CLICK
- INSUFFICIENT_EVIDENCE

Findings remain distinct from Diagnosis.


## Sprint4.2 Differential Diagnosis

Doctor now produces ranked diagnostic hypotheses with confidence, support, contradiction,
and full traceability.

Initial candidates:

- LOW_CTR_WITH_STRONG_POSITION
- LONG_TERM_DECLINE
- CONTENT_STALE
- UPDATE_FAILURE
- INSUFFICIENT_DATA

These candidates are not yet Final Diagnoses.


## Sprint4.3 Final Diagnosis

Doctor now records CONFIRMED or DEFERRED final diagnosis outcomes.


## Sprint5.1 Treatment Recommendation and Referral

Doctor now converts the latest Final Diagnosis into a separate treatment direction and referral.

Active routing:

- confirmed CTR, decline, stale-content, and update-failure diagnoses → Writer
- deferred diagnoses → Observation / follow-up

Creator, Merge, noindex, and delete routing remain reserved for later diagnosis expansion.


## Sprint6.1 Search Console 365-Day Acquisition

Doctor now contains a provider-neutral acquisition service and Google API adapter for:

- 28-day aggregate metrics
- 90-day aggregate metrics
- 365-day aggregate metrics
- paged query-level metrics
- retry and partial-failure reporting
- conversion into the existing Search Console Observation contract

Credentials and OAuth UI are intentionally excluded.


## Sprint6.2 SERP Observation

Doctor now supports provider-neutral SERP acquisition and Medical Record snapshots.

Recorded data includes:

- top results
- search intent
- SERP features
- competition strength
- changes from the previous SERP snapshot

SERP data now enables the Competition Resilience Vital Sign.


## Sprint6.3 Article Snapshot Observation

Doctor now records article structure and content metadata as an immutable snapshot.

This enables the final previously unavailable Vital Sign:

- Content Integrity

All seven Vital Signs can now be represented when the required observations exist.


## Sprint6.4 Clinical Pipeline

Doctor now includes an end-to-end orchestrator that coordinates:

Observation → Evidence → Vital Signs → Findings → Differential Diagnosis →
Final Diagnosis → Treatment Recommendation → Referral.

Each component remains independent and idempotent.


## Sprint6.5 Diagnosis Report and Output

Doctor now produces:

- a plain-language user diagnosis report
- `SIMS_DOCTOR_SINGLE_CASE_RESULT_V1`
- `SIMS_DOCTOR_WRITER_REQUEST_V1` for confirmed Writer referrals

The Medical Record, diagnosis report, and referral request remain separate artifacts.


## Sprint7.1 Cross-Article Diagnosis

Doctor can now compare articles within the same site and diagnose:

- Cannibalization
- Article Merge Required
- New Article Needed

This activates Creator and Merge as real referral targets.


## Sprint7.2 Long-Term Decline Diagnosis

Doctor now analyzes repeated 28-day windows over 365 days and distinguishes:

- Long-Term Decay
- Seasonal Decline
- Recovery in Progress

Confirmed long-term decay routes to Writer.
Seasonal and recovery cases route to Observation.


## Sprint7.3 Improvement History Comparison

Doctor now compares pre-treatment metrics with 7, 14, and 28-day checkpoints and distinguishes:

- Treatment Success
- Improvement Failure
- Post-Improvement Worsening
- Mixed Treatment Response
- Follow-Up Required

Worsening and ineffective treatment route to Writer. Doctor never rolls back an article automatically.


## Sprint7.4 Longitudinal Medical Record

Doctor now analyzes repeated diagnoses and treatment responses for the same article.

It can identify recurrent or chronic problems, treatment responsiveness or resistance,
recovery patterns, and follow-up priority.


## Sprint8.1 Batch Doctor Foundation

Doctor can now accept many articles in one request, prioritize them, execute each article
as an isolated Case, continue after individual failures, and resume a previous batch.

Persistent scheduling and worker infrastructure are not included yet.


## Sprint8.2 Persistent Batch Queue

Doctor now contains a storage-neutral persistent queue and nightly worker foundation.

It supports durable checkpoints, lease locks, retries, pause/resume, incomplete-batch discovery,
and completion events. Production database and scheduler adapters remain deployment tasks.


## Sprint8.3 Production Queue and Scheduler

Doctor now includes a durable SQLite queue adapter and an automation-friendly scheduler CLI.
A paused batch can survive process restart and resume from its saved checkpoint.


## Sprint8.4 SBM Batch Integration

Doctor now defines the complete JSON-contract flow for SBM batch submission, acceptance,
progress polling, terminal result export, and idempotent result import acknowledgement.

The integration does not expose Doctor Medical Records or internal diagnosis rules.


## Sprint8.5 SBM–Doctor Transport API

Doctor now provides an authenticated transport layer for SBM batch submission, status polling,
and result retrieval.

Requests use HMAC-SHA256 signatures, timestamps, nonces, per-client rate limits, and
idempotency keys. A WSGI adapter is included for deployment integration.


## Sprint8.6 Production Security Persistence

Doctor now persists nonce replay protection, API idempotency responses, and audit logs in SQLite.

A production application factory loads secrets from environment variables and exposes liveness
and readiness endpoints. Real secrets are never stored in the repository.


## Sprint9.1 Diagnostic Rule Engine

Doctor now supports declarative, explainable diagnostic rules.

Rules can evaluate Evidence, Findings, Vital Signs, Observations, Longitudinal Profiles,
Treatment History, and case context, then produce prioritized diagnosis candidates without
directly creating treatment or referral instructions.


## Sprint9.2 Vital Score Engine

Doctor now calculates a 0–100 article health score from the seven Vital Signs.

The score supports missing-sign reweighting, LOW_SAMPLE and serious-Finding adjustments,
health bands, and explainable positive and negative factors.


## Sprint9.3 Improvement Failure Diagnosis

Doctor now integrates treatment history, Vital Score changes, metric deterioration,
recurrence, and LOW_SAMPLE safeguards to distinguish no effect, worsening, possible
wrong treatment direction, recurrent failure, and insufficient follow-up.


## Sprint9.4 Long-Term Degradation Diagnosis

Doctor now integrates 365-day trend data, Vital Score changes, recurrence, seasonality,
recovery, and LOW_SAMPLE safeguards to distinguish chronic degradation, sharp degradation,
CTR degradation, position degradation, seasonal variation, and recovery.


## Sprint9.5 CTR Opportunity Diagnosis

順位別期待CTR、Winner Query保護、直近タイトル変更、LOW_SAMPLEを統合しました。


## Sprint9.6 Position Opportunity Diagnosis

Doctor now identifies articles with meaningful impressions that remain near page one,
including high opportunity, query-focused opportunity, Winner Query protection,
and low-visibility or intent-misalignment cases.


## Sprint9.7 Intent Drift Diagnosis

Doctor now compares current query demand with article identity through query clusters,
intent shares, entropy, title overlap, emerging-intent growth, and Winner Query protection.


## Sprint9.8 Freshness Decay Diagnosis

Doctor now distinguishes local factual decay from severe article-wide freshness decay,
while protecting Winner Queries and recently updated articles.


## Sprint9.9 Cannibalization Diagnosis

記事間の共通クエリ、SERP、検索意図、流入差から統合候補と役割分担を診断します。


## Sprint10.0 Composite Diagnosis

Doctor now integrates all specialist assessments into one final diagnosis.

Safety rules for LOW_SAMPLE, recent changes, Winner Queries, Merge candidates, and role
separation take precedence over weighted scoring.


## Sprint10.1 Treatment Recommendation

Doctor now converts Composite Diagnosis into target-specific referrals for Writer, Creator,
Merge, observation, or follow-up while preserving treatment safety boundaries.


## Sprint10.2 Doctor Report Generator

利用者向け診断書とシステム向け構造化レポートを分離しました。


## Sprint10.3 Explainable Diagnosis

Doctor now records a user-facing decision path and a separate system audit trail.


## v1.0.0-RC1

The complete Doctor workflow is frozen as a release candidate for end-to-end acceptance testing.


## v1.0.1 行動優先型出力
利用者向け診断は「今回やること」から開始し、利用者が次の担当製品へ直接渡せる依頼文を含みます。
## v1.5.1 LOW_SAMPLE SERP fallback
When Search Console evidence is too sparse for a reliable outcome judgment, aDoctor now treats low sample as an evidence limitation rather than treatment failure. It can fall back to target-query SERP competitiveness review, distinguish actionable SERP gaps from sufficient competitiveness or low demand, and return low-demand/low-priority cases as normal close candidates instead of repeatedly rewriting them.

