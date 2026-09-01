# SIMS Article Doctor Interface Contract Registry v0.1.0

## Contracts

| Contract | Source | Target | Responsibility |
|---|---|---|---|
| SIMS_DOCTOR_ARTICLE_CATALOG_V1 | SIMS_BLOG_MANAGER | SIMS_DOCTOR | 記事マスタと運用状態 |
| SIMS_DOCTOR_LONG_TERM_SNAPSHOT_V1 | SIMS_DOCTOR_COLLECTOR | SIMS_DOCTOR_DIAGNOSIS_ENGINE | 長期集計とデータ品質 |
| SIMS_DOCTOR_CASE_DIAGNOSIS_V1 | SIMS_DOCTOR | SIMS_BLOG_MANAGER | 診断Case・治療案・ロック要求 |
| SIMS_DOCTOR_WRITER_REQUEST_V1 | SIMS_DOCTOR | SIMS_WRITER | Writer向け個別Treatment |
| SIMS_TREATMENT_RESULT_V1 | 専門システム | SIMS_DOCTOR | 個別Treatment結果 |
| SIMS_DOCTOR_CASE_RESULT_V1 | SIMS_DOCTOR | SIMS_BLOG_MANAGER | Case全体の集約結果 |

## Core rules

- `site_id` と `article_id` の正本は SBM。
- `case_id` と `treatment_id` の発行主体は Doctor。
- `message_id` は送信元内で一意。
- 同一 `message_id` は冪等に無視。
- Case状態 `TREATING` と Treatment状態 `IN_PROGRESS` を混同しない。
- 公開判断と公開状態を分離する。
- 未知の任意フィールドは無視できる。
- 未知の列挙値は既知値へ自動変換しない。
