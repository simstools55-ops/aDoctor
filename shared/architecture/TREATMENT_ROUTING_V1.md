# Doctor Treatment Routing v1

- Existing single-article change: Writer.
- Independent new intent or topic gap: Creator.
- Multi-URL competition, duplication, consolidation, redirect/noindex/delete planning: Merge.
- Low sample, recent publication/treatment, unresolved seasonality, or indexing transition: Monitor.
- Healthy, aligned, or risk-exceeds-benefit: No Action.
- Post-treatment decline requires Doctor re-examination before another Writer treatment.
- Referrals are recommendations; SBM validates Workflow Lock, evidence, dependencies, user approval, and compatibility before issuing a request.

## Treatment Strategy layer

Doctor may attach one platform-visible Treatment Strategy above the existing treatment level/scope.

- `WAIT`: do not initiate material treatment yet; define observation targets and re-examination timing.
- `LIGHT_FIX`: limited, low-risk correction such as factual freshness, title/meta/FAQ or narrowly scoped alignment.
- `NORMAL_REWRITE`: ordinary Writer-level treatment within an SBM-issued allowed scope.
- `FULL_REWRITE`: broad restructuring or extensive rewrite is justified by integrated evidence.

Treatment Strategy does not bypass Routing. Doctor returns it to SBM; SBM decides whether and when to issue Writer, Creator, or Merge work.

`WAIT` is an active monitoring strategy, not a synonym for no evidence review or indefinite inaction.

