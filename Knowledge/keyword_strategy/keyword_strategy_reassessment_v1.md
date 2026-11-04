# Keyword Strategy Reassessment v1 — aDoctor v2.0.4

This policy applies ONLY after the existing SIMS Manager request gate and Evidence Validation succeed for a normal SEO diagnosis. It does not change the information-update dedicated reception or other contracts.

## Three distinct fields
- original_target_query: article creation intent, only when explicitly evidenced; otherwise null. Never infer it from current GSC.
- observed_main_query: Manager/GSC observation, read-only; do not overwrite or redefine it.
- improvement_target_query: Doctor's recommended next optimization focus; nullable when article-role separation or evidence insufficiency makes a single focus inappropriate.

## Four outcomes
- MAINTAIN: preserve original intent and article role when still appropriate.
- RETARGET: change the optimization focus only if repeated sufficient observations, SERP intent, article content and site portfolio support it; never rewrite GSC observations.
- ROLE_SEPARATION: preserve hub/specialist boundaries; route distinct search intents to existing specialist articles or recommend new ones only after verified independent demand and cannibalization checks.
- DEFER: insufficient or contradictory evidence; avoid irreversible title/URL/content changes and specify missing evidence.

## Evidence and risk controls
Reuse existing intent_drift, cannibalization, position and CTR policies and LOW_SAMPLE protection. Compare query impressions, clicks, CTR, position trend, observed periods, SERP intent, existing article roles, and monetization opportunity where evidence exists. Do not treat a top GSC query as the creation-time target. Revenue at query level is not observable from GSC; describe indirect opportunity as estimated, not measured. Do not fabricate original keyword, numerical confidence, rankings, revenue, or sibling article performance. Prefer reversible internal-link adjustments to broad rewrites when evidence is mixed.

## Output (optional, backward compatible)
When the SEO case involves a meaningful discrepancy between original intent and observed query, include a compact top-level keyword_strategy_assessment in SIMS_DOCTOR_CASE_RESULT_V2:
- decision: MAINTAIN | RETARGET | ROLE_SEPARATION | DEFER
- original_target_query: string|null
- observed_main_query: string|null
- improvement_target_query: string|null
- article_role: string|null
- reason: concise Japanese text grounded in evidence
- confidence: CONFIRMED | PROVISIONAL | INSUFFICIENT
- evidence_gaps: array of strings (optional)
Do not change workflow_handoff.next_action or treatment_plan strategy enumerations. This assessment is strategic metadata, not a new workflow state. Keep the JSON compact; Manager's Doctor result storage has a size limit. Never modify Manager article-management fields or GSC source data.

## Example A000185
Beginner hub, observed query 'notion 重い 開かない', links to three specialist pages already implemented: provisional ROLE_SEPARATION; original target and improvement target null until independently evidenced. Do not prescribe another edit merely because the assessment exists.


## V2 JSON contract guard — v2.0.5
- Managerへ登録する通常診断の最終JSONは `SIMS_DOCTOR_CASE_RESULT_V2.schema.json` に従い、少なくとも `format`, `contract_version`, `case_id`, `article_id`, `diagnosis`, `treatment_plan`, `referral`, `workflow`, `reexamination` を必ず含める。`referral` は `required`, `destination`, `allowed_scope`, `blocked_scope` を含み、`workflow` は `workflow_locked` と `return_to: SIMS_BLOG_MANAGER` を含める。
- `keyword_strategy_assessment` は任意で、存在する場合は **次の7項目を必須**とする: `decision` (MAINTAIN / RETARGET / ROLE_SEPARATION / DEFER), `original_target_query` (文字列またはnull), `observed_main_query` (文字列またはnull), `improvement_target_query` (文字列またはnull), `article_role` (文字列またはnull), `reason` (空でない文字列), `confidence` (CONFIRMED / PROVISIONAL / INSUFFICIENT)。任意で `evidence_gaps` (文字列配列) を付けられる。
- **禁止**: このオブジェクト内で `confidence: 0.8` のような数値、`original_target` や `gsc_observed_main_query` や `doctor_improvement_target` の入れ子オブジェクト、`role_assignments` 等の未定義キーを出さない。数値確信度や詳細根拠は従来の `diagnosis` や説明文に置く。
- GSC観測値を推測した当初狙い語で置き換えない。観測クエリの出典が曖昧なら `observed_main_query: null` とし `evidence_gaps` に記す。記事の役割から戦略を確定できる場合、当初狙い語がnullでもROLE_SEPARATIONを許容する。
- **検証専用モード**: 既存Caseの判定確認を求められ、Managerへ登録しない場合、通常診断JSONの代わりに `keyword_strategy_assessment` 単独のJSONを「検証用・登録不可」と明記して出す。既存の `workflow_handoff.next_action` をコピーした登録可能そうなV2 JSONを作らない。既存の処置を再実行・再登録しない。
- 通常診断と情報更新専用受付の契約は従来どおり維持し、情報更新専用受付にはこの戦略評価を適用しない。
