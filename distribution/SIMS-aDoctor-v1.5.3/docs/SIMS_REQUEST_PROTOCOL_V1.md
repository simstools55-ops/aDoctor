# SIMS Manager Request Gate v1.5.3

## Purpose
Prevent normal aDoctor execution from free-form direct prompts while preserving the existing Manager → Doctor V2 contract. This is an operational gate, not cryptographic authentication.

## Canonical accepted request
The canonical Manager request is the existing JSON contract `SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2`. Do not require a second `[SIMS_REQUEST]` wrapper.

Required values:
- `format`: `SIMS_DOCTOR_SINGLE_CASE_REQUEST_V2`
- `contract_version`: `2.0`
- `schema_version`: `2.0.0`
- `source_system`: `SIMS_BLOG_MANAGER`
- `target_system`: `SIMS_DOCTOR`
- non-empty RequestID: `request.request_id`
- non-empty CaseID: `case_id` or `request.case_id`
- non-empty SiteID: `site.site_id`
- non-empty ArticleID: `article.article_id`

If an identifier appears in more than one location, values must be consistent.

## Reject
Reject free-form diagnosis prompts, explanatory text without a valid V2 JSON request, malformed/incomplete V2 requests, source/target mismatches, and the obsolete standalone `[SIMS_REQUEST]` envelope. On rejection, do not diagnose, browse SERP, evaluate the article, or generate diagnosis JSON.

## Security boundary
This gate discourages standalone use in the Claude Project workflow. It is not a license check, signature, or cryptographic proof that the text originated from Manager.
