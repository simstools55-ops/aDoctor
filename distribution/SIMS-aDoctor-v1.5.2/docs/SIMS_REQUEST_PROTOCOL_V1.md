# SIMS Request Protocol v1

## Purpose

SIMS Request Protocol is the operational request envelope used between SIMS Manager and a-series specialist products. It is an execution gate, not License Center authentication and not cryptographic proof.

For aDoctor, normal diagnostic execution requires a Manager-issued envelope with the following shape:

```text
[SIMS_REQUEST]
PROTOCOL=SIMS-A/1
SOURCE=SIMS_MANAGER
EDITION=FULL
TARGET=ADOCTOR
REQUEST_TYPE=ARTICLE_DIAGNOSIS
REQUEST_ID=<Manager RequestID>
CASE_ID=<Manager CaseID>
SITE_ID=<Manager SiteID>
ARTICLE_ID=<Manager ArticleID>
[/SIMS_REQUEST]
```

## aDoctor acceptance rules

The request is accepted only when all of the following are true:

- `PROTOCOL` exactly equals `SIMS-A/1`.
- `SOURCE` exactly equals `SIMS_MANAGER`.
- `EDITION` exactly equals `FULL`.
- `TARGET` exactly equals `ADOCTOR`.
- `REQUEST_TYPE` exactly equals `ARTICLE_DIAGNOSIS`.
- `REQUEST_ID`, `CASE_ID`, `SITE_ID`, and `ARTICLE_ID` are non-empty.
- If the same identifiers also occur in the request body or Evidence Package, they are consistent with the envelope.

If validation fails, aDoctor must not start diagnosis, Web/SERP research, article evaluation, treatment planning, or diagnosis-result JSON generation. The normal user-facing warning is:

> この依頼はSIMS Managerから発行された正規のaDoctor診断依頼として確認できません。SIMS ManagerのaDoctor精密診断から依頼文を作成し、その依頼文を使用してください。

A new diagnostic case requires a new valid envelope even if an earlier turn in the same conversation contained one.

## Security boundary

This protocol is prompt/workflow-level operational control for Claude Project deployments. It does not replace SIMS License Center, does not cryptographically authenticate Manager, and cannot guarantee resistance against a user who can alter Project Instructions. A future signed transport may reuse this envelope as the signed payload.

## Compatibility

- SIMS Shared Editorial Knowledge remains 3.5.0.
- Existing aDoctor diagnostic contracts and result contracts are unchanged.
- License Center does not need an aDoctor-specific license record.
- Manager FULL/STARTER edition control remains the product-entitlement boundary; this protocol controls normal request entry into aDoctor.
